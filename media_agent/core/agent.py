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
1.  **Intent Interpretation**: When a user expresses a desire to "watch" an item (e.g., "我想看..."), your first and only initial action **MUST** be to use a search tool (`search_movie` or `search_series`). **Do not** assume you know what the user wants, even for famous titles. Always search first to get accurate information.
2.  **Complete Execution**: You must complete all steps in the user's request. If a user asks to search and then download, you must search before downloading.
3.  **Factual Reporting**: Your final answer must be based on the information returned by the tools. If content already exists or an error occurs, report it truthfully.
4.  **Handling Search Results**:
    *   If a search returns multiple items, you **MUST** list all results for the user to choose from. **Do not** guess, assume, or download anything.
    *   If you are not confident which item the user wants, you **MUST** ask for clarification.
5.  **Action Confirmation**: After a successful `download_movie` or `download_series` call, you **MUST** consider the task complete. **Do not** use any queue-checking tools for verification. Immediately report to the user that the item has been added and the system is searching for it.
6.  **Search and Retry Logic**: If a search fails, you may try again once. If the second attempt also fails, you must stop and report the failure to the user. Do not attempt to search more than twice for the same request.
7.  **Output Format**: Adhere strictly to this format.
    *   **Tool Calls**: When you need to call a tool, your response **MUST** contain *only* the tool call object. Do not include any other text, commentary, or explanation in your response.
    *   **Final Answers**: When the task is complete, you are asking a question, or reporting a failure, your response **MUST** be plain, natural language. It **MUST NOT** contain any JSON objects or tool call syntax like `{{...}}` in the end of your response.
8.  **Language**: You must respond in the same language the user is using.
9.  **Functionality Limitations**: You can only perform actions supported by your available tools. If a user asks for something you cannot do (like downloading a single episode, deleting a file, or canceling a download), you must clearly state that you lack that capability. For TV series, specify that you can only download by full seasons.
"""
        
        example_messages = []

        # Scenario 1: Successful download after user confirmation (single result)
        search_call_1_id = "tool_call_search_1"
        download_call_1_id = "tool_call_download_1"
        example_messages.extend([
            HumanMessage(content="Please download the show 'TV Show A', seasons 1 and 2."),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_series", "args": {"query": "TV Show A"}, "id": search_call_1_id}]
            ),
            ToolMessage(
                content="Found one series: Title: TV Show A, Year: 2010, TVDB ID: 81189",
                tool_call_id=search_call_1_id
            ),
            AIMessage(
                content="I found 'TV Show A' from 2010. Should I proceed with downloading seasons 1 and 2?"
            ),
            HumanMessage(content="Yes, go ahead."),
            AIMessage(
                content="",
                tool_calls=[{"name": "download_series", "args": {"tvdb_id": 81189, "seasons": [1, 2]}, "id": download_call_1_id}]
            ),
            ToolMessage(
                content="Successfully added the series to Sonarr.",
                tool_call_id=download_call_1_id
            ),
            AIMessage(content="Alright, I've added the download task for seasons 1 and 2 of 'TV Show A'. The system is now searching for the episodes.")
        ])

        # Scenario 2: Successful download after user clarification (multiple results)
        search_call_2_id = "tool_call_search_2"
        download_call_2_id = "tool_call_download_2"
        example_messages.extend([
            HumanMessage(content="I want to download all seasons of 'TV Show C'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_series", "args": {"query": "TV Show C"}, "id": search_call_2_id}]
            ),
            ToolMessage(
                content="Found the following series:\n  - Title: TV Show C, Year: 2011, TVDB ID: 121361\n  - Title: TV Show C: The Last Watch, Year: 2019, TVDB ID: 365888",
                tool_call_id=search_call_2_id
            ),
            AIMessage(content="I found a couple of shows. Which one did you mean?\n- TV Show C (2011)\n- TV Show C: The Last Watch (2019)"),
            HumanMessage(content="The one from 2011."),
            AIMessage(
                content="",
                tool_calls=[{"name": "download_series", "args": {"tvdb_id": 121361, "seasons": "all"}, "id": download_call_2_id}]
            ),
            ToolMessage(
                content="Successfully added the series to Sonarr for all seasons.",
                tool_call_id=download_call_2_id
            ),
            AIMessage(content="Great! I've set up the download for all seasons of 'TV Show C' (2011). The system is now searching for the episodes.")
        ])

        # Scenario 3: Download after user clarification (ambiguous query)
        search_call_3_id = "tool_call_search_3"
        download_call_3_id = "tool_call_download_3"
        example_messages.extend([
            HumanMessage(content="我要下载电影'电影三部曲A'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_movie", "args": {"query": "电影三部曲A"}, "id": search_call_3_id}]
            ),
            ToolMessage(
                content="搜索到以下电影:\n  - 标题: 电影三部曲A：第一部, 年份: 2001, TMDB ID: 120\n  - 标题: 电影三部曲A：第二部, 年份: 2002, TMDB ID: 121\n  - 标题: 电影三部曲A：第三部, 年份: 2003, TMDB ID: 122",
                tool_call_id=search_call_3_id
            ),
            AIMessage(content="我找到了多部与'电影三部曲A'相关的电影，请问您具体想下载哪一部？\n- 电影三部曲A：第一部 (2001)\n- 电影三部曲A：第二部 (2002)\n- 电影三部曲A：第三部 (2003)"),
            HumanMessage(content="第二部"),
            AIMessage(
                content="",
                tool_calls=[{"name": "download_movie", "args": {"tmdb_id": 121}, "id": download_call_3_id}]
            ),
            ToolMessage(
                content="电影已成功添加到Radarr。",
                tool_call_id=download_call_3_id
            ),
            AIMessage(content="好的，我已经将《电影三部曲A：第二部》加入了下载队列。")
        ])

        # Scenario 4: Download special episodes after user confirmation
        search_call_4_id = "tool_call_search_4"
        download_call_4_id = "tool_call_download_4"
        example_messages.extend([
            HumanMessage(content="帮我下载'电视剧D'的特别节目"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_series", "args": {"query": "电视剧D"}, "id": search_call_4_id}]
            ),
            ToolMessage(
                content="搜索到以下电视剧: 标题: 电视剧D, 年份: 2015, TVDB ID: 273181",
                tool_call_id=search_call_4_id
            ),
            AIMessage(content="我找到了《电视剧D》(2015)，需要我为您下载它的特别节目吗？"),
            HumanMessage(content="是的"),
            AIMessage(
                content="",
                tool_calls=[{"name": "download_series", "args": {"tvdb_id": 273181, "seasons": [0]}, "id": download_call_4_id}]
            ),
            ToolMessage(
                content="已成功将特别节目添加到Sonarr。",
                tool_call_id=download_call_4_id
            ),
            AIMessage(content="好的，我已经添加了《电视剧D》特别节目的下载任务。")
        ])
        
        # Scenario 5: Search fails and aborts
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

        # Scenario 6: Search for a movie only, no download intent
        search_call_6_id = "tool_call_search_6"
        example_messages.extend([
            HumanMessage(content="Help me see if there is a movie called 'Movie E'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_movie", "args": {"query": "Movie E"}, "id": search_call_6_id}]
            ),
            ToolMessage(
                content="Found the following movie: Title: Movie E, Year: 2014, TMDB ID: 157336",
                tool_call_id=search_call_6_id
            ),
            AIMessage(content="Yes, I found the movie 'Movie E' from 2014.")
        ])

        # Scenario 7: User requests an unsupported action (downloading an episode)
        example_messages.extend([
            HumanMessage(content="帮我下载《电视剧F》第五季第二集。"),
            AIMessage(content="很抱歉，我无法下载特定的单集。我只能按季下载。需要我为您下载《电视剧F》第五季的整季吗？")
        ])

        # Scenario 8: User requests an unsupported action (deleting a movie)
        example_messages.extend([
            HumanMessage(content="请帮我删除电影资料库里的《电影G》。"),
            AIMessage(content="对不起，我没有删除媒体文件的功能。")
        ])

        # Scenario 9: User expresses intent to watch a movie, leading to search, clarification, and download
        search_call_watch_id = "tool_call_search_watch"
        example_messages.extend([
            HumanMessage(content="我想看电影'一部精彩的电影'"),
            AIMessage(
                content="",
                tool_calls=[{"name": "search_movie", "args": {"query": "一部精彩的电影"}, "id": search_call_watch_id}]
            ),
            ToolMessage(
                content="搜索到以下电影:\n  - 标题: 一部精彩的电影, 年份: 2022, TMDB ID: 789\n  - 标题: 一部精彩的电影：续集, 年份: 2024, TMDB ID: 790",
                tool_call_id=search_call_watch_id
            ),
            AIMessage(content="我找到了几部相关的电影，请问您想看哪一部？\n- 一部精彩的电影 (2022)\n- 一部精彩的电影：续集 (2024)")
        ])

        # Scenario 9 Follow-up: User confirms and agent downloads
        download_call_watch_id = "tool_call_download_watch"
        example_messages.extend([
            HumanMessage(content="2022年的那部"),
            AIMessage(
                content="",
                tool_calls=[{"name": "download_movie", "args": {"tmdb_id": 789}, "id": download_call_watch_id}]
            ),
            ToolMessage(
                content="Successfully added the movie to Radarr...",
                tool_call_id=download_call_watch_id
            ),
            AIMessage(content="好的，我已经将'一部精彩的电影' (2022)加入了下载队列，系统现在会开始寻找资源。")
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
