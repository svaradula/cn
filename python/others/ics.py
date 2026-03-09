from datetime import datetime, timedelta

# Settings
start_date = datetime(2026, 2, 23, 18, 0) # Today at 18:00
total_days = 100
title_prefix = "Coding Challenge"

ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Coding Challenge//100 Days//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH"
]

for i in range(1, total_days + 1):
    current_start = start_date + timedelta(days=i-1)
    current_end = current_start + timedelta(hours=2)
    
    # Format dates for ICS (YYYYMMDDTHHMMSS)
    dtstart = current_start.strftime("%Y%m%dT%H%M%S")
    dtend = current_end.strftime("%Y%m%dT%H%M%S")
    uid = f"cc-{i}-{current_start.strftime('%Y%m%d')}@challenge.com"
    
    ics_content.append("BEGIN:VEVENT")
    ics_content.append(f"SUMMARY:{title_prefix} - {i}/100")
    ics_content.append(f"DTSTART:{dtstart}")
    ics_content.append(f"DTEND:{dtend}")
    ics_content.append(f"UID:{uid}")
    ics_content.append(f"DESCRIPTION:Day {i} of 100.")
    ics_content.append("BEGIN:VALARM")
    ics_content.append("ACTION:NONE")
    ics_content.append("END:VALARM")
    ics_content.append("END:VEVENT")

ics_content.append("END:VCALENDAR")

# Write to file
with open("coding_challenge.ics", "w") as f:
    f.write("\n".join(ics_content))

print("File 'coding_challenge.ics' created successfully!")