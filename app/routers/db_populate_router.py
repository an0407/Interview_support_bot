# from sqlalchemy.ext.asyncio import AsyncSession
# from fastapi import APIRouter, Depends
# from datetime import datetime, timezone, timedelta

# from app.models.db.employee_model import Employee
# from app.database import get_async_session

# router = APIRouter(prefix='/populate_employees', tags=['populate_employees'])

# @router.post('/', response_model=dict)
# async def populate_employees(db: AsyncSession = Depends(get_async_session)):
#     names = [
#         "Abhisheke Karthi", "Aravindan K", "Bharath Senthil", "Devaraj M", "Guhan Tamilvanan",
#         "Hari K", "Jayanth Reddy", "Kamalesh R", "Kamesh Dillibabu", "Mohamed Althaf",
#         "Pragatheeshwara", "Pugazhendhi K", "Rajesh N", "Robson Dias A", "santhoshshivan k",
#         "Sathishkumar Ravi", "Siddiq Ab", "Sri Murugan G", "Sudharsan Senthil", "Tamizhan M",
#         "Tamizhelvan A", "Thukkamuthu BS", "vignesh sivanesan", "Vinothkumar .e"
#     ]

#     joining_date = datetime.now().date() - timedelta(days=90)  # 3 months ago

#     employees = []
#     for i, full_name in enumerate(names, start=1):
#         parts = full_name.split(' ', 1)
#         first_name = parts[0]
#         last_name = parts[1] if len(parts) > 1 else ''

#         employee = Employee(
#             first_name=first_name,
#             last_name=last_name,
#             joining_date=joining_date,
#             experience=3,
#             email=f"{first_name.lower()}.{i}@example.com",  # dummy unique email
#             interview_count=0,
#             created_at=datetime.now(timezone.utc),
#             updated_at=None
#         )
#         employees.append(employee)

#     db.add_all(employees)
#     await db.commit()

#     return {"message": f"{len(employees)} employees inserted successfully."}


from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from datetime import datetime

from app.models.db.admin_model import Admin
from app.models.db.employee_model import Employee
from app.database import get_async_session

router = APIRouter(prefix='/create_admin', tags = ['create_admin'])

@router.post('/', response_model = dict)
async def create_admin(db: AsyncSession = Depends(get_async_session)):
    # data = Employee(first_name = 'Anush', last_name = 'MN', email = 'anush.softsuave@gmail.com', 
    #                 joining_date=datetime.strptime('2025/04/02', '%Y/%m/%d').date(), experience=3)
    data = Admin(first_name = 'def', last_name = 'Doe', email = 'def@gmail.com')
    db.add(data)
    await db.commit()
    await db.refresh(data)
    return {'message' : 'admin created'}