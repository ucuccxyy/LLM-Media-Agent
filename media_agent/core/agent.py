"""
主Agent逻辑
"""

import sys
import os
from typing import Dict, Any, List, Union

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool, BaseTool
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from uuid import uuid4

from media_agent.tools import radarr_tool, sonarr_tool, qbittorrent_tool
from media_agent.core.llm_manager import OllamaManager
from media_agent.tools.sonarr_tool import DownloadSeriesInput

class MediaAgent:
    """媒体管理Agent主类"""
    
    def __init__(self, llm_manager: OllamaManager, settings):
        self.llm_manager = llm_manager
        self.settings = settings
        
        # Tools are now self-contained, no need to pass services
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent()
    
    def _create_tools(self) -> list[BaseTool]:
        """Creates and returns all media management tools."""
        @tool
        def search_movie(query: str) -> str:
            """
            Searches for a movie by its title.
            Args:
                query (str): The title of the movie to search for.
            Returns:
                A list of found movies with their titles, years, and TMDB IDs.
            """
            return radarr_tool.search_movie_logic(query)

        @tool
        def download_movie(tmdb_id: int) -> str:
            """
            Adds a movie to Radarr by its TMDB ID and starts the download.
            Args:
                tmdb_id (int): The TMDB ID of the movie to download.
            Returns:
                A confirmation message indicating success or failure.
            """
            return radarr_tool.download_movie_logic(tmdb_id)

        @tool
        def search_series(query: str) -> str:
            """
            Searches for a TV series by its title.
            Args:
                query (str): The title of the series to search for.
            Returns:
                A list of found series with their titles, years, and TVDB IDs.
            """
            return sonarr_tool.search_series_logic(query)

        @tool(args_schema=DownloadSeriesInput)
        def download_series(tvdb_id: int, seasons: Union[str, list[int]]) -> str:
            """
            Adds a TV series to Sonarr by its TVDB ID and specifies which seasons to download.
            Args:
                tvdb_id (int): The TVDB ID of the series.
                seasons (Union[str, list[int]]): Either a list of season numbers to download (e.g., [1, 2, 3]) or the string 'all' to download all seasons. For special episodes, use seasons=[0].
            Returns:
                A confirmation message indicating success or failure.
            """
            return sonarr_tool.download_series_logic(tvdb_id, seasons)
        
        @tool
        def get_sonarr_queue() -> str:
            """
            Checks the Sonarr download queue to see the status of currently downloading series.
            Returns:
                A summary of the items in the Sonarr download queue.
            """
            return sonarr_tool.get_sonarr_queue_logic()

        # Assuming radarr_tool will also have a get_radarr_queue_logic
        @tool
        def get_radarr_queue() -> str:
            """
            Checks the Radarr download queue to see the status of currently downloading movies.
            Returns:
                A summary of the items in the Radarr download queue.
            """
            # This function needs to be implemented in radarr_tool.py
            # For now, let's assume it exists or add a placeholder.
            if hasattr(radarr_tool, 'get_radarr_queue_logic'):
                return radarr_tool.get_radarr_queue_logic()
            return "Radarr queue checking is not yet implemented."

        @tool
        def get_torrents() -> str:
            """Gets the list and status of all current torrents."""
            return qbittorrent_tool.get_torrents_logic()

        return [
            search_movie,
            download_movie,
            search_series,
            download_series,
            get_sonarr_queue,
            get_radarr_queue,
            get_torrents,
        ]

    def _create_agent(self):
        """创建Agent"""
        
        system_prompt = """You are a media management assistant. Your goal is to use the available tools to fulfill the user's request.

**Rules:**
1.  **Complete Execution**: You must complete all steps in the user's request. If a user asks to search and then download, you must search before downloading.
2.  **Factual Reporting**: Your final answer must be based on the information returned by the tools. If content already exists or an error occurs, report it truthfully.
3.  **Confident Decision Making**: Your primary goal is to successfully complete the user's request without unnecessary questions.
    *   **Act decisively**: After searching, examine the **first** result. If its title is a clear, case-insensitive match for what the user requested, you **MUST** ignore all other items in the list and proceed with the download immediately. For instance, if the user asks for "series_a" and the first result is "Series_A" (even if other results like "Series B" or "The Series A" are present), you must treat it as a perfect match and download it.
    *   **Ask only when necessary**: Only ask for clarification if the first result is clearly different from the user's request. For example, if the user requests "Movie B" and the result is "Movie B: The Sequel", you should ask for confirmation.
    *   **Handle Ambiguity**: If the search returns multiple relevant but non-perfect matches, you **MUST** list the top results for the user to choose from. For example, a search for "Movie C" might return all three movies in the trilogy.
4.  **Action Confirmation**: After a successful `download_movie` or `download_series` call, you **MUST** consider the task complete. **Do not** use any queue-checking tools for verification. Immediately report to the user that the item has been added and the system is searching for it.
5.  **Search and Retry Logic**: You may encounter issues with non-English titles. Follow this logic strictly:
    *   **First Attempt**: Always perform the search as requested.
    *   **Chinese Title Retry**: If the first search was for a title in Chinese and it failed, you **MUST** immediately try to search for the *exact same Chinese title* a second time. This is a mandatory retry.
    *   **Give Up**: If the search fails for a non-Chinese title, or if the second attempt for a Chinese title also fails, you must stop and report the failure. Do not attempt to search more than twice for the same request.
6.  **Output Format**: Adhere strictly to this format.
    *   **Tool Calls**: When you need to call a tool, your response **MUST** contain *only* the tool call object. Do not include any other text, commentary, or explanation in your response.
    *   **Final Answers**: When the task is complete, you are asking a question, or reporting a failure, your response **MUST** be plain, natural language. It **MUST NOT** contain any JSON objects or tool call syntax like `{{...}}` in the end of your response.
7.  **Language**: You must respond in the same language the user is using.
8.  **Functionality Limitations**: You can only perform actions supported by your available tools. If a user asks for something you cannot do (like downloading a single episode, deleting a file, or canceling a download), you must clearly state that you lack that capability. For TV series, specify that you can only download by full seasons.
9.  **Mandatory Chinese Title Retry**: This is a critical and non-negotiable rule. If a `search_movie` or `search_series` call with a Chinese `query` fails, you **MUST** immediately retry the *exact same search* one more time. Do not ask the user for more information or give up before this mandatory second attempt.
"""
        
        example_messages = []

        # Scenario: Chinese search fails on first attempt and succeeds on retry
        search_cn_fail_id = "tool_call_search_cn_fail"
        search_cn_retry_id = "tool_call_search_cn_retry"
        example_messages.extend([
            HumanMessage(content="帮我找一下电影《阿凡达》"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_movie", "args": {"query": "阿凡达"}, "id": search_cn_fail_id}]
            ),
            ToolMessage(
                content="No movie found for '阿凡达'.",
                tool_call_id=search_cn_fail_id
            ),
            # Model sees the Chinese title search failed, so it immediately retries.
            AIMessage(
                content="",
                tool_calls=[{"name": "search_movie", "args": {"query": "阿凡达"}, "id": search_cn_retry_id}]
            ),
            ToolMessage(
                content="Found the following movie: Title: Avatar, Year: 2009, TMDB ID: 19995",
                tool_call_id=search_cn_retry_id
            ),
            AIMessage(content="好的，我找到了电影《阿凡达》（2009）。")
        ])

        # Scenario 1: Successful end-to-end task (download and verify) - General Case
        search_call_1_id = "tool_call_search_1"
        example_messages.extend([
            HumanMessage(content="Please find the show 'TV Show A' and download seasons 1 and 2 for me."),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_series", "args": {"query": "TV Show A"}, "id": search_call_1_id}]
            ),
            ToolMessage(
                content="Found the following series:\n  - Title: TV Show A...",
                tool_call_id=search_call_1_id
            )
        ])
        download_call_1_id = "tool_call_download_1"
        example_messages.extend([
            AIMessage(
                content="",
                tool_calls=[{"name": "download_series", "args": {"tvdb_id": 81189, "seasons": [1, 2]}, "id": download_call_1_id}]
            ),
            ToolMessage(
                content="Successfully added the series to Sonarr...",
                tool_call_id=download_call_1_id
            ),
            AIMessage(content="Alright, I've found 'TV Show A' and added the download tasks for seasons 1 and 2. The system is now searching for the episodes to download.")
        ])

        # Scenario 1.5: Confident download for case-insensitive match ("the boys" example)
        search_call_boys_id = "tool_call_search_boys"
        example_messages.extend([
            HumanMessage(content="Please help me search for and download season 1 of the TV show 'tv show b'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_series", "args": {"query": "tv show b"}, "id": search_call_boys_id}]
            ),
            ToolMessage(
                content="Found the following series:\n  - Title: TV Show B, Year: 2019, TVDB ID: 355567\n  - Title: Show B, Year: 2022, TVDB ID: 423151\n  - Title: TV Show B (1993), Year: 1993, TVDB ID: 77590",
                tool_call_id=search_call_boys_id
            )
        ])
        download_call_boys_id = "tool_call_download_boys"
        example_messages.extend([
            AIMessage(
                content="",
                tool_calls=[{"name": "download_series", "args": {"tvdb_id": 355567, "seasons": [1]}, "id": download_call_boys_id}]
            ),
            ToolMessage(
                content="Successfully added the series to Sonarr...",
                tool_call_id=download_call_boys_id
            ),
            AIMessage(content="Alright, I've found 'TV Show B' and added the download task for season 1. The system is now searching for the episode to download.")
        ])

        # Scenario 1.6: Download all seasons example
        search_call_all_id = "tool_call_search_all"
        example_messages.extend([
            HumanMessage(content="I want to download all seasons of 'TV Show C'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_series", "args": {"query": "TV Show C"}, "id": search_call_all_id}]
            ),
            ToolMessage(
                content="Found the following series:\n  - Title: TV Show C, Year: 2011, TVDB ID: 121361\n  - Title: TV Show C: The Last Watch, Year: 2019, TVDB ID: 365888",
                tool_call_id=search_call_all_id
            )
        ])
        download_call_all_id = "tool_call_download_all"
        example_messages.extend([
            AIMessage(
                content="",
                tool_calls=[{"name": "download_series", "args": {"tvdb_id": 121361, "seasons": "all"}, "id": download_call_all_id}]
            ),
            ToolMessage(
                content="Successfully added the series to Sonarr and started searching for all seasons...",
                tool_call_id=download_call_all_id
            ),
            AIMessage(content="Great! I've found 'TV Show C' and set up the download for all seasons. The system is now searching for the episodes.")
        ])

        # Scenario 2: Search result does not exactly match, requires user confirmation
        search_call_2_id = "tool_call_search_2"
        example_messages.extend([
            HumanMessage(content="Help me download season 1 of 'Movie Trilogy A'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_series", "args": {"query": "Movie Trilogy A"}, "id": search_call_2_id}]
            ),
            ToolMessage(
                content="Found the following series: Title: Movie Trilogy A: The Spinoff Series, Year: 2022, TVDB ID: 367506 ...",
                tool_call_id=search_call_2_id
            ),
            AIMessage(content="I found a series called 'Movie Trilogy A: The Spinoff Series,' which seems to be the most relevant result for 'Movie Trilogy A.' Would you like me to download the first season of this show?")
        ])

        # Scenario 2 Follow-up: User confirms and agent downloads
        download_call_2_id = "tool_call_download_2"
        example_messages.extend([
            HumanMessage(content="是的，帮我下载这部剧。"),
            AIMessage(
                content="",
                tool_calls=[{"name": "download_series", "args": {"tvdb_id": 367506, "seasons": [1]}, "id": download_call_2_id}]
            ),
            ToolMessage(
                content="Successfully added the series to Sonarr...",
                tool_call_id=download_call_2_id
            ),
            AIMessage(content="好的，我已经将《电影三部曲A：衍生剧》第一季加入了下载队列，系统现在会开始寻找资源。")
        ])

        # Scenario 2.2: Ambiguous search with multiple results
        search_call_lotr_id = "tool_call_search_lotr"
        example_messages.extend([
            HumanMessage(content="我要下载电影'电影三部曲A'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_movie", "args": {"query": "电影三部曲A"}, "id": search_call_lotr_id}]
            ),
            ToolMessage(
                content="搜索到以下电影:\n  - 标题: 电影三部曲A：第一部, 年份: 2001, TMDB ID: 120\n  - 标题: 电影三部曲A：第二部, 年份: 2002, TMDB ID: 121\n  - 标题: 电影三部曲A：第三部, 年份: 2003, TMDB ID: 122",
                tool_call_id=search_call_lotr_id
            ),
            AIMessage(content="我找到了多部与'电影三部曲A'相关的电影，请问您具体想下载哪一部？\n- 电影三部曲A：第一部 (2001)\n- 电影三部曲A：第二部 (2002)\n- 电影三部曲A：第三部 (2003)")
        ])

        # Scenario 2.5: Successfully download special episodes
        search_call_special_id = "tool_call_search_special"
        example_messages.extend([
            HumanMessage(content="帮我下载'电视剧D'的特别节目"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_series", "args": {"query": "电视剧D"}, "id": search_call_special_id}]
            ),
            ToolMessage(
                content="搜索到以下电视剧: 标题: 电视剧D, 年份: 2015, TVDB ID: 273181 ...",
                tool_call_id=search_call_special_id
            ),
            AIMessage(
                content="",
                tool_calls=[{"name": "download_series", "args": {"tvdb_id": 273181, "seasons": [0]}, "id": "tool_call_download_special"}]
            )
        ])
        
        # Scenario 3: Search fails and aborts
        # First attempt
        search_fail_1_id = "tool_call_search_fail_1"
        example_messages.extend([
            HumanMessage(content="Help me find a movie called 'A Non-Existent Movie'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_movie", "args": {"query": "A Non-Existent Movie"}, "id": search_fail_1_id}]
            ),
            ToolMessage(
                content="No movie found for 'A Non-Existent Movie'.",
                tool_call_id=search_fail_1_id
            )
        ])
        # Second attempt
        search_fail_2_id = "tool_call_search_fail_2"
        example_messages.extend([
            AIMessage(
                content="",
                tool_calls=[{"name": "search_movie", "args": {"query": "A Non-Existent Movie"}, "id": search_fail_2_id}]
            ),
            ToolMessage(
                content="No movie found for 'A Non-Existent Movie'.",
                tool_call_id=search_fail_2_id
            ),
            AIMessage(content="I'm sorry, but I couldn't find a movie called 'A Non-Existent Movie'.")
        ])

        # Scenario 4: Search for a movie only
        search_call_4_id = "tool_call_search_4"
        example_messages.extend([
            HumanMessage(content="Help me see if there is a movie called 'Movie E'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_movie", "args": {"query": "Movie E"}, "id": search_call_4_id}]
            ),
            ToolMessage(
                content="Found the following movie: Title: Movie E, Year: 2014, TMDB ID: 157336 ...",
                tool_call_id=search_call_4_id
            ),
            AIMessage(content="Found the movie 'Movie E' from 2014.")
        ])

        # Scenario 5: User requests an unsupported action (downloading an episode)
        example_messages.extend([
            HumanMessage(content="帮我下载《电视剧F》第五季第二集。"),
            AIMessage(content="很抱歉，我无法下载特定的单集。我只能按季下载。需要我为您下载《电视剧F》第五季的整季吗？")
        ])

        # Scenario 6: User requests an unsupported action (deleting a movie)
        example_messages.extend([
            HumanMessage(content="请帮我删除电影资料库里的《电影G》。"),
            AIMessage(content="对不起，我没有删除媒体文件的功能。")
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
        ] + example_messages + [
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_tool_calling_agent(self.llm_manager.llm, self.tools, prompt)
        
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入，并返回Agent的最终响应。
        """
        try:
            response = self.agent_executor.invoke({"input": user_input})
            return response
        except Exception as e:
            return {"error": f"处理请求时发生错误: {str(e)}"}
