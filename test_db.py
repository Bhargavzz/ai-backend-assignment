from app.database import engine, Base
from app import models
from sqlalchemy import text

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 'SUCCESS:  CONNECTED TO MySQL'"))
        print(result.scalar())
except Exception as e:
    print(f"FAILURE: {e}")

print("Creating tables...")

try:
    # Checks models and creates the tables in MySQL if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Tables created Succesfully")

    # Verification
    with engine.connect() as conenction:
        result = connection.execute(text("SHOW TABLES;"))
        print("\nExisting Tables:")
        for row in result:
            print(f"- {row[0]}")

except Exception as e:
    print(f"Error: {e}")