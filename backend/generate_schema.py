from app.database import engine
from app.models.models import Base
from sqlalchemy.schema import CreateTable

with open("../schema.sql", "w") as f:
    f.write("-- Krishi Setu Database Schema\n")
    f.write("-- Generated from SQLAlchemy models\n\n")
    for table in Base.metadata.sorted_tables:
        f.write(str(CreateTable(table).compile(engine)).strip() + ";\n\n")

print("schema.sql generated successfully") 
