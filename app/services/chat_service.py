from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory

from app.models.pydantic.chat_payload import AdminPayload
from app.utils.tools import (set_db_session, send_otp, verify_otp, schedule_interview, check_interview, get_interview_requirements, volunteer_interview, show_volunteers,
                             finalize_volunteers, end_interview)
from app.services.memory_manager import MemoryManager

load_dotenv()

#initialize the llm
llm = ChatOpenAI(model = 'gpt-4o-mini')

class ChatService():
    def __init__(self, db: AsyncSession):
        set_db_session(db)
        self.tools = [send_otp, verify_otp, schedule_interview, check_interview, get_interview_requirements, volunteer_interview, show_volunteers, 
                      finalize_volunteers, end_interview]
        self.prompt = hub.pull("hwchase17/openai-functions-agent")
        self.memory_manager = MemoryManager(db)
        self.agent = create_openai_functions_agent(
            llm=llm,
            tools=self.tools,
            prompt=self.prompt
        )

    async def chat(self, chat_data: AdminPayload) -> dict:
        try:
            # Load history for memory context
            history = await self.memory_manager.get_history(chat_data.session_id)

            # Reconstruct memory
            memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
            for user, bot in history:
                memory.chat_memory.add_user_message(user)
                memory.chat_memory.add_ai_message(bot)

            agent_executor = AgentExecutor.from_agent_and_tools(
                agent=self.agent,
                tools=self.tools,
                memory=memory,
                handle_parsing_errors=True,
                max_iterations=10
            )

            response = await agent_executor.ainvoke({'input': chat_data.query})

            # Save message to DB
            await self.memory_manager.save_message(
                session_id=chat_data.session_id,
                user_input=chat_data.query,
                assistant_response=response['output']
            )

            return {"response": response['output']}
        except Exception as e:
            return {"response": f"Sorry, I encountered an error: {str(e)}"}
