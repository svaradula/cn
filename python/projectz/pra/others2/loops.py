users = ["Manava", "Rani", "Priya", "Georgia"]
transactions = [100, 200, 300]

# for user in users:
#     for attempt in range(1, 3):
#         print(f"Attempt {attempt}: Sending welcome and instruction email-set")
#         print(f"sent email to {user}")
#         print("------ ----------- ----------")

logs = ["INFO", "DEBUG", "ERROR", "INFO"]

for log in logs:
    if log == "ERROR":
        print("Critical issue found!")
        break


attempts = 0
success = False

while attempts < 3:
    password = input("Enter password : ")
    print(logs)
    if(password == "test"):
        success = True
        logs.remove('ERROR')
        break;
    attempts += 1

if(success):
    transactions.append(500)
    print("Issue cleared..")
    print(logs)
else:
    print("invalid password. Issue not cleared")


records = ["valid", "", "valid", None]

for record in records:
    if not record:
        continue
    print(f"Processing record: {record}")


for amount in transactions:
    if amount == 500:
        print("Transaction found")
        break
else:
    print("Transaction not found")


users = ["active", "inactive", "active"]

active_users = [s for s in users if s == "active"]

print(active_users)