# app/utils/tools.py
from langchain.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc
from datetime import date, datetime
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from app.models.db.admin_model import Admin
from app.models.db.interview_model import Interview
from app.models.db.temp_model import Temp
from app.models.db.employee_model import Employee
from app.models.db.memory_model import ChatHistory
    
load_dotenv()

# Create a global variable to inject the DB session
DB_SESSION: AsyncSession | None = None

def set_db_session(session: AsyncSession):
    global DB_SESSION
    DB_SESSION = session

# @tool
# def validate_query(query: str) -> bool:
#     """
#     Checks if the given query is a valid intent for the interview selection bot.
#     Returns True if it's about interview or volunteer-related intent.
#     """
#     llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
 
#     prompt = f"""
# You are an intent classifier.
# Just answer with "yes" or "no". Don't use any other words strictly.
 
# Determine if the user's message is related to:
# - Requesting volunteers for an interview
# - Conducting or organizing interviews
# - General volunteers enquiring about scheduled interviews
 
# If yes, respond only with: yes  
# If not, respond only with: no
 
# Query: "{query}"
 
# Answer:
# """
#     response = llm.invoke(prompt)
#     print("[inside tool - response]", response.content)
#     return response.content.strip().lower() == "yes"

@tool("schedule_interview", description=f"This tool can be used when a user wants to schedule/create a new interview. Note: Today's date is {date.today().isoformat()}")
async def schedule_interview(level1: int, level2: int, interviewdate: str, email: str) -> dict:
    """
        This tool inserts a column in the 'interviews' table based on the user's request.

        args:
            - level1: number of volunteers needed for l1(or user might mention level 1) support, 0 if user says no level1 volunteers are needed
            - level2: number of volunteers needed for l2(or user may mention level 2) support, 0 if user says no level2 volunteers are needed
            - date: the date on which the interview is scheduled (must be a valid future date)
            - email: email of the admin user who scheduled the interview

        Returns:
            dict: JSON response for interview scheduled or not authorised message

        Raises:
            Exception: If the external API call fails
        """
    try:
        if DB_SESSION is None:
            return {"error": "DB session not initialized"}
        
        result = await DB_SESSION.execute(
        select(ChatHistory).order_by(desc(ChatHistory.created_at)).limit(1)
        )
        latest_record = result.scalar_one_or_none()
        if(email != latest_record.session_id):
            return {'Response' : 'You can not provide the email of another user, email must be same as entered in "session ID"'}

        result = await DB_SESSION.execute(select(Admin).where(Admin.email == email))
        admin = result.scalar_one_or_none()
        print()
        print(f"admin: {admin.__dict__}")
        print()
        if not admin:
            return {"response": "this email is not allowed to schedule interview"}

        parsed_date = datetime.strptime(interviewdate, "%Y-%m-%d").date()
        print()
        print(f"parsed_date: {parsed_date}")
        print()

        result = await DB_SESSION.execute(select(Interview).where(Interview.interview_date == parsed_date))
        interview = result.scalar_one_or_none()
        if interview:
            return {"response" : "interview is already scheduled on this day"}

        interview = Interview(
            admin_id=admin.id,
            l1_count=level1,
            l2_count=level2,
            interview_date=parsed_date,
            is_active=True
        )
        DB_SESSION.add(interview)
        await DB_SESSION.commit()
        await DB_SESSION.refresh(interview)

        return {"message": "interview scheduled successfully"}
    except Exception as e:
        return {"error": "Exception", "details": str(e)}
    
@tool("check_interview", description = 'this tool can be used to check for active interviews/schedules interviews and tell the user')
async def check_interview():
    result = await DB_SESSION.execute(select(Interview).where(Interview.is_active == True))
    interviews = result.scalars().all()

    if not interviews:
        return {'response' : 'no active interviews'}
    else:
        interview_dates = [interview.interview_date for interview in interviews]
        return {'response' : f'yes, there are interviews scheduled on {interview_dates}'}
    
@tool('get_interview_requirements', description='This tool can be used when the user asks about the requirements of a particular or group of interviews')
async def get_interview_requirements(dates : list):
    """
    This tool gets the requirements of scheduled interviews using the list of interview dates

    args: 
        - dates : list of dates of interviews of which the user has asked details of. list stores single date if the user asks requirements
            of a particular interview or else stores the dates of all interviews that the user has asked details of

    returns:
        - response: requirements of all scheduled interviews
    raises: 
        - Exception:  If the external API call fails
    """
    try: 
        interviews = []
        for day in dates:
            parsed_date = datetime.strptime(day, "%Y-%m-%d").date()
            result = await DB_SESSION.execute(select(Interview).where(Interview.interview_date == parsed_date))
            interview = result.scalar_one_or_none()
            interviews.append({
                'interview_date' : interview.interview_date,
                'l1_requirement' : f'{interview.l1_count} person(s) needed',
                'l2_requirement' : f'{interview.l2_count} people(s) needed'
            })
        return {'response' : f'these are the requirements of the interview(s): \n {interviews}'}
    except Exception as e:
        return {"error": "Exception", "details": str(e)}



    
@tool("volunteer_interview", description="This tool can be used to create a new volunteer using their email, date of interview and level of interview they want to support")
async def volunteer_interview(email : str, day : str, level : str):
    """
    This tool inserts a column in the 'temporary' table based on the user's request.

    args:
            - email: email of the volunteer who makes the request
            - day: the date of interview for which the user is volunteering
            - level: the level of the interview for which the user is volunteering. If user says 
                        'level1' or 'level 1' or 'l1' or similar as level = '1' and 
                        'level2' or 'level 2' or 'l2' or similar as level = '2'
    Returns:
            dict: JSON response for volunteer request added or not allowed to volunteer

    Raises:
            Exception: If the external API call fails
    """
    print()
    print(email)
    print()
    print(type(level), level)
    print()
    
    try:
        result = await DB_SESSION.execute(
        select(ChatHistory).order_by(desc(ChatHistory.created_at)).limit(1)
        )
        latest_record = result.scalar_one_or_none()
        if(email != latest_record.session_id):
            return {'Response' : 'You can not provide the email of another user, email must be same as entered in "session ID"'}
        
        parsed_date = datetime.strptime(day, "%Y-%m-%d").date()
        result = await DB_SESSION.execute(select(Interview).where(Interview.interview_date == parsed_date))
        interview = result.scalar_one_or_none()

        if not interview:
            return {'response' : f'no interview scheduled on {parsed_date}'}
        
        result = await DB_SESSION.execute(select(Employee).where(Employee.email == email))
        employee = result.scalar_one_or_none()

        if not employee:
            return {'response' : 'this email is not allowed to volunteer for interview support'}
        elif employee:
            if(level in ('2','level 2', 'level2', 'l2') and employee.experience < 6):
                return {'response' : 'you do not have enough experience to volunteer for l2 support, you can volunteer for l1 instead'}
            
        if(level in ('1','level 1', 'level1', 'l1') and interview.l1_count == 0):
            return {'response' : 'there is no requirement for l1 support for this interview'}
        if(level in ('2','level 2', 'level2', 'l2') and interview.l2_count == 0):
            return {'response' : 'there is no requirement for l2 support for this interview'}
        
        result = await DB_SESSION.execute(select(Admin).where(Admin.id == interview.admin_id))
        admin = result.scalar_one_or_none()

        temporary = Temp(
            first_name = employee.first_name,
            last_name = employee.last_name,
            email = email,
            level_chosen = level,
            admin_email = admin.email,
            interview_count = employee.interview_count
        )
        print()
        print(temporary)
        print()

        DB_SESSION.add(temporary)
        await DB_SESSION.commit()

        return {'repsonse' : 'volunteer request added successfully'}
    except Exception as e:
        return {"error": "Exception", "details": str(e)}
    
@tool('show_volunteers', description='this tool can be used to show all the volunteers when the admin asks')
async def show_volunteers(email : str):
    """
    This tool checks who and all have applied for interview 
    from the 'temporary' table where the admin_email is the current user's(admin's) email.

    args: 
        - email: email of the admin who started the interview, which must strictly be given by admin when he asks who and all applied
        , else u must ask him for email
    
    returns: 
        - dict: the employees who have applied for the interview support or no volunteers
    
    raises: 
        - exception: If the external API call fails
    """
    if not email:
        return {'response' : 'provide your email id'}
    result = await DB_SESSION.execute(
        select(ChatHistory).order_by(desc(ChatHistory.created_at)).limit(1)
        )
    latest_record = result.scalar_one_or_none()
    if(email != latest_record.session_id):
        return {'Response' : 'You can not provide the email of another user, email must be same as entered in "session ID"'}
    
    result = await DB_SESSION.execute(select(Temp).where(Temp.admin_email == email))
    applicants = result.scalars().all()
    
    if not applicants:
        return {'response': 'No volunteers have applied yet.'}

    # Convert each applicant object to a dictionary
    applicant_list = [
        {
            "first_name": a.first_name,
            "last_name": a.last_name,
            "email": a.email,
            "level_chosen" : a.level_chosen,
            "interview_count": a.interview_count,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in applicants
    ]

    return {'volunteers': applicant_list}

@tool('finalize_volunteers', description='this tool can be used when the user selects the final volunteers from the list of volunteers')
async def finalize_volunteers(volunteer_emails : list):
    """
    args: 
        - volunteer_emails: list of emails of the selected volunteers"""
    for email in volunteer_emails:
        await DB_SESSION.execute(
            update(Employee)
            .where(Employee.email == email)
            .values(interview_count=Employee.interview_count + 1))
    return {'response' : 'email sent to the selected volunteers! Do you want to end the volunteering process?'}


@tool('end_interview', description='this tool can be used when a user confirms that they want to end the interview volunteering process')
async def end_interview(email : str):
    """
    This tool deletes all values from the temporary table and sets 'is_active' = False in the interviews table
    if email is validated as admin email

    args:
            - email: email of the admin who makes the interview end request
    
    Returns:
            dict: JSON response for interview end request, ended or not allowed to end

    Raises:
            Exception: If the external API call fails
    """
    result = await DB_SESSION.execute(
        select(ChatHistory).order_by(desc(ChatHistory.created_at)).limit(1)
        )
    latest_record = result.scalar_one_or_none()
    if(email != latest_record.session_id):
        return {'Response' : 'You can not provide the email of another user, email must be same as entered in "session ID"'}
    result = await DB_SESSION.execute(select(Admin).where(Admin.email == email))
    admin = result.scalar_one_or_none()
    
    if not admin:
        return {"response": "Unauthorized to end interview volunteering"}
    
    
    result = await DB_SESSION.execute(
        update(Interview)
        .where(Interview.admin_id == admin.id)
        .values(is_active=False)
    )
    await DB_SESSION.commit()

    
    await DB_SESSION.execute(delete(Temp).where(Temp.admin_email == email))
    await DB_SESSION.commit()

    return {'response' : 'Successfully ended the interview volunteering process'}