# app/utils/tools.py
from langchain.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc
from datetime import date, datetime
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import smtplib
import random

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

def send_email(receiver_email : str, subject: str, message : str):
    text = f"subject: {subject}\n\n{message}"
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login('anush.softsuave@gmail.com', 'mzss rirg ugqu dwgk')
    server.sendmail('anush.softsuave@gmail.com', receiver_email, text)

otp_list = [123456]
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

@tool('send_otp', description="this tool must be strictly called whenever a user mentions their email id or when the user's otp is not verified")
def send_otp(receiver_email: str):
    """
    This tool is used to send an otp to the email mentioned by the user as their email

    args:
        - receiver_email : The email that the user mentions as their email

    returns:
        - response : otp sent to ur email, send it here to verify email
    """
    otp = random.randint(100000,999999)
    otp_list[0] = otp
    send_email(receiver_email=receiver_email, subject='OTP', message=f'your otp is {otp}')
    return {'response' : 'otp sent to ur email, send it here to verify email'}

@tool('verify_otp', description="This tool can be used to verify the otp that the user returns")
def verify_otp(otp : int):
    """
    This tool is used to verify the otp sent to the user's email, that the user sends back to verify their email

    args:
        - otp : The number that the user mentions as their received otp

    returns:
        - response : otp matched, email is verified or otp mismatched, confirm the new otp sent to ur email
    """
    if(otp == otp_list[0]):
        return {'response' : 'otp matches, your email id is verified'}
    return {'response' : 'otp mismatched, resend your correct email id'}


@tool("schedule_interview", description=f"This tool can be used when a user wants to schedule/create a new interview if their email has been verified, else don't run this tool yet even if all the variables required for this tool are already provided by the user Note: Today's date is {date.today().isoformat()}")
async def schedule_interview(email: str, level1_volunteers_count: int, level2_volunteers_count: int, interviewdate: str, 
                             last_date_to_volunteer : str) -> dict:
    """
        This tool inserts a column in the 'interviews' table based on the user's request.

        args:
            - email: email of the admin user who scheduled the interview
            - level1_volunteers_count: number of volunteers needed for l1(or user might mention level 1 or similar terms) support, 0 if user says no level1 volunteers are needed
            - level2_volunteers_count: number of volunteers needed for l2(or user may mention level 2 or similar terms) support, 0 if user says no level2 volunteers are needed
            - date: the date on which the interview is scheduled (must be a valid future date)
            - last_date_to_volunteer: The last date before which the employees may submit their volunteering request
        Returns:
            dict: JSON response for interview scheduled or not authorised message

        Raises:
            Exception: If the external API call fails
        """
    print()
    print(email, level1_volunteers_count, level2_volunteers_count, interviewdate)
    print()
    try:
        if DB_SESSION is None:
            return {"error": "DB session not initialized"}

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

        last_date = datetime.strptime(last_date_to_volunteer, "%Y-%m-%d").date()

        result = await DB_SESSION.execute(select(Interview).where(Interview.interview_date == parsed_date, Interview.is_active == True))
        interview = result.scalar_one_or_none()
        if interview:
            return {"response" : "interview is already scheduled on this day"}
        else:
            send_email(receiver_email=email, subject='Interview Scheduled Successfully', message=f"""The interview has been 
                       successfully scheduled on {interviewdate}, with requirements - L1:{level1_volunteers_count}, 
                       L2:{level2_volunteers_count}.
                        \n\nRegards\nInterview Suppport Chatbot""")
            result = await DB_SESSION.execute(select(Employee))
            employees = result.scalars().all()
            for employee in employees:
                send_email(receiver_email=employee.email, subject='New Interview Scheduled', message=f"""An interview has been scheduled on 
                        {parsed_date}.\n you can contact the "interview support chatbot" if you want to know details of interview or volunteer
                        for the interview support. Last Date for submitting volunteering interest is {last_date}.
                        \n\nRegards\n{admin.first_name} {admin.last_name}""")
            interview = Interview(
                admin_id=admin.id,
                l1_count=level1_volunteers_count,
                l2_count=level2_volunteers_count,
                interview_date=parsed_date,
                is_active=True
            )
            DB_SESSION.add(interview)
            await DB_SESSION.commit()
            await DB_SESSION.refresh(interview)
            return {"message": "interview scheduled successfully, and mail sent to all eligible candidates"}
    except Exception as e:
        return {"error": "Exception", "details": str(e)}
    
@tool("check_interview", description = 'this tool can be used to check for active interviews/schedules and tell the user when they enquire to know if any interviews are there/active or even if they say they want to apply/volunteer for an interview')
async def check_interview():
    result = await DB_SESSION.execute(select(Interview).where(Interview.is_active == 1))
    interviews = result.scalars().all()

    if not interviews:
        return {'response' : 'no active interviews'}
    else:
        active_interviews = [{
                'interview_date' : interview.interview_date,
                'l1_requirement' : f'{interview.l1_count} person(s) needed',
                'l2_requirement' : f'{interview.l2_count} people(s) needed'
            } for interview in interviews]
        return {'response' : f'yes, there are interviews scheduled on the following days with the respective requirements: {active_interviews}'}
    
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



    
@tool("volunteer_interview", description="This tool can be used when a user wants to volunteer or apply for an interview, to create a new volunteer using their email and date of interview only if their email has been verified. If not don't run this tool yet even if all the variables required for this tool are already provided by the user.")
async def volunteer_interview(email : str, day : str):
    """
    This tool inserts a column in the 'temporary' table based on the user's request, user is automatically 
    matched to level 1 or 2 based on their experience that we can check using their email.

    args:
            - email: email of the volunteer who makes the request
            - day: the date of interview for which the user is volunteering
    Returns:
            dict: JSON response for volunteer request added or not allowed to volunteer

    Raises:
            Exception: If the external API call fails
    """
    print()
    print(email)
    print()
    
    try:
        parsed_date = datetime.strptime(day, "%Y-%m-%d").date()
        result = await DB_SESSION.execute(select(Interview).where(Interview.interview_date == parsed_date))
        interview = result.scalar_one_or_none()

        if not interview:
            return {'response' : f'no interview scheduled on {parsed_date}'}
        
        result = await DB_SESSION.execute(select(Temp).where(Temp.email == email, Temp.interview_date == parsed_date))
        temp = result.scalar_one_or_none()
        if temp:
            return {'response' : 'You have already applied for volunteering for an interview on this day'}
        
        result = await DB_SESSION.execute(select(Employee).where(Employee.email == email))
        employee = result.scalar_one_or_none()

        result = await DB_SESSION.execute(select(Admin).where(Admin.id == interview.admin_id))
        admin = result.scalar_one_or_none()

        if not employee:
            return {'response' : 'this email is not allowed to volunteer for interview support'}
        elif employee:
            if(employee.experience == 3 and interview.l1_count > 0):
                temporary = Temp(
                first_name = employee.first_name,
                last_name = employee.last_name,
                email = email,
                level_chosen = 'L1',
                interview_date = parsed_date,
                admin_email = admin.email,
                interview_count = employee.interview_count
                )
                send_email(receiver_email= email, subject='Requested for Volunteering', message=f"""You have successfully submitted your request 
                    for volunteering for L1 support on {day}\n\nregards:\nInterview support bot""")
            
                DB_SESSION.add(temporary)
                await DB_SESSION.commit()

                return {'repsonse' : 'volunteer request added successfully, you would have received a confirmation email'}
            elif(employee.experience == 6 and interview.l2_count > 0):
                temporary = Temp(
                first_name = employee.first_name,
                last_name = employee.last_name,
                email = email,
                level_chosen = 'L2',
                interview_date = parsed_date,
                admin_email = admin.email,
                interview_count = employee.interview_count
                )
                send_email(receiver_email= email, subject='Requested for Volunteering', message=f"""You have successfully submitted your request 
                    for volunteering for L2 support on {day}\n\nregards:\nInterview support bot""")
            
                DB_SESSION.add(temporary)
                await DB_SESSION.commit()

                return {'repsonse' : 'volunteer request added successfully, you would have received a confirmation email'}
            elif(employee.experience == 6 and interview.l2_count == 0 and interview.l1_count > 0):
                temporary = Temp(
                first_name = employee.first_name,
                last_name = employee.last_name,
                email = email,
                level_chosen = 'L1',
                interview_date = parsed_date,
                admin_email = admin.email,
                interview_count = employee.interview_count
                )
                send_email(receiver_email= email, subject='Requested for Volunteering', message=f"""You have successfully submitted your request 
                    for volunteering for L1 support on {day}\n\nregards:\nInterview support bot""")
            
                DB_SESSION.add(temporary)
                await DB_SESSION.commit()

                return {'repsonse' : 'volunteer request added successfully for L1 since you are eligible for L1 also. This is because there are no requirements for l2 for this interview, you would have received a confirmation email'}
            else:
                return {'response' : f'there are no requirements for the level you are eligible for in interview on {parsed_date}'}
    except Exception as e:
        return {"error": "Exception", "details": str(e)}
    
@tool('show_volunteers', description='this tool can be used to show all the volunteers when the admin asks only if their email has been verified')
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

@tool('finalize_volunteers', description="this tool can be used whenever the user's message hints that they are selecting a particular or group of candidates(example: send confirmation email to the first guy or send confirmation email to the first 4 guys, or anything else that suggests that the admin is selecting a list of candidates or one of the candidates), only if the user's email has been verified")
async def finalize_volunteers(volunteer_emails : list):
    """
    args: 
        - volunteer_emails: list of emails of the selected volunteers
    """
    for email in volunteer_emails:
        send_email(receiver_email=email, subject= 'Volunteer Request Approved', message='Your request for interview support has been approved\n\nRegards:\nInterview support Chatbot ')
        await DB_SESSION.execute(
            update(Employee)
            .where(Employee.email == email)
            .values(interview_count=Employee.interview_count + 1))
    return {'response' : 'email sent to the selected volunteers! Do you want to end the volunteering process?'}


@tool('end_interview', description='this tool can be used when a user confirms that they want to end the interview volunteering process only if thier email is verified')
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