CREATE TABLE IF NOT EXISTS customers (
    "Date" DATE,
    "CustomerId" BIGINT PRIMARY KEY,
    "Surname" TEXT,
    "CreditScore" INTEGER,
    "Geography" TEXT,
    "Gender" TEXT,
    "Age" INTEGER,
    "Tenure" INTEGER,
    "Balance" NUMERIC(15,2),
    "NumOfProducts" INTEGER,
    "HasCrCard" INTEGER,
    "IsActiveMember" INTEGER,
    "EstimatedSalary" NUMERIC(15,2),
    "Exited" INTEGER
);