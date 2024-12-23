import calendar
import requests
from datetime import datetime


API_KEY = ""    # Put your api key, which can be obtained here https://app.clockify.me/user/preferences#advanced
BASE_URL = "https://api.clockify.me/api/v1/"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
current_datetime = datetime.now()


def main():
    if not API_KEY:
        raise Exception("Use your api key - https://app.clockify.me/user/preferences#advanced")

    session = requests.Session()
    session.headers.update({"x-api-key": API_KEY})

    user_url = f"{BASE_URL}/user"
    user_response = session.get(user_url).json()
    user_name = user_response["name"]
    user_email = user_response["email"]
    user_id = user_response["id"]
    workspace_id = user_response["activeWorkspace"]

    projects_url = f"{BASE_URL}/workspaces/{workspace_id}/projects"
    projects_response = session.get(projects_url).json()

    projects = {}
    for project in projects_response:
        projects[project["name"]] = project["id"]

    print(f"User: {user_name} - {user_email}")
    projects_names = ', '.join(str(key) for key in projects)
    print(f"Projects: {projects_names}")

    project_id = input_project_name(projects)
    month = input_month()
    year = input_year()
    last_month_day = calendar.monthrange(year, month)[1]
    start_datetime = datetime(year, month, 1, 0, 0, 0)
    end_datetime = datetime(year, month, last_month_day, 23, 59, 59)

    time_entries_url = f"{BASE_URL}/workspaces/{workspace_id}/user/{user_id}/time-entries"
    time_entries_params = {
        "project": project_id,
        "start": start_datetime.strftime(DATE_FORMAT),
        "end": end_datetime.strftime(DATE_FORMAT),
        "page-size": 5000
    }
    time_entries_response = session.get(time_entries_url, params=time_entries_params).json()

    total_time = 0
    date_dict = {}
    task_dict = {}
    for time_entry in time_entries_response:
        description = time_entry["description"]
        time_interval = time_entry["timeInterval"]
        start_datetime = datetime.strptime(time_interval["start"], DATE_FORMAT)
        end_datetime = datetime.strptime(time_interval["end"], DATE_FORMAT)
        time_diff = (end_datetime - start_datetime).seconds / 60 / 60
        total_time += time_diff

        if start_datetime.day < 10:
            start_day = f"0{start_datetime.day}"
        else:
            start_day = f"{start_datetime.day}"
        if start_datetime.month < 10:
            start_month = f"0{start_datetime.month}"
        else:
            start_month = f"{start_datetime.month}"

        date = f"{start_day}.{start_month}"
        if date in date_dict:
            date_dict[date] += time_diff
        else:
            date_dict[date] = time_diff
        if description in task_dict:
            task_dict[description] += time_diff
        else:
            task_dict[description] = time_diff

    if not date_dict:
        print(f"No records for {month}/{year}")
        return

    print("--------------------------------------------------------------------------------")
    print(f"\nSummary for {calendar.month_name[month]} {year}")
    total_time_by_date_dict = sum(date_dict.values())
    total_time_by_task_dict = sum(task_dict.values())
    if total_time_by_date_dict != total_time_by_task_dict:
        print(f"\nWarning: total time by dates ({total_time_by_date_dict}) is different than total time by tasks ({total_time_by_task_dict})")
    else:
        print(f"\nTotal time: {total_time_by_date_dict} h")

    sorted_task_dict = dict(reversed(sorted(task_dict.items(), key=lambda item: sort_tasks(item[0]))))
    joined_tasks = ", ".join(sorted_task_dict.keys())
    print(f"Task list: {joined_tasks}")
    print("\nWorktime by dates:\n")
    for key, value in reversed(date_dict.items()):
        print(f"{key} - {value} h")
    print("\n\nWorktime by tasks:\n")
    for key, value in sorted_task_dict.items():
        print(f"{key} - {value} h")


def input_project_name(projects):
    project_input = input("\nType project name to generate summary: ")
    if project_input in projects:
        return projects[project_input]
    else:
        print(f"Project {project_input} not found in user projects")
        return input_project_name(projects)


def input_month():
    last_month = current_datetime.month-1 if current_datetime.month > 1 else 12
    month_input = input(f"\nType month or press enter to generate summary for {calendar.month_name[last_month]} ")
    month_int = int(month_input) if month_input else None
    if not month_input or month_int < 1 or month_int > 12:
        return last_month
    else:
        return month_int


def input_year():
    year_input = input(f"\nType year or press enter to generate summary for year {current_datetime.year} ")
    year_int = int(year_input) if year_input else None
    if not year_input:
        return current_datetime.year
    else:
        return year_int


# define your sorting order of tasks - greater number is higher at the list
def sort_tasks(name):
    lower_name = name.lower()
    if lower_name.startswith("amok"):
        return 0
    if lower_name.startswith("hd"):
        return 1
    if lower_name.startswith("mob"):
        return 2
    if lower_name.startswith("amk"):
        return 3
    return 1000


if __name__ == '__main__':
    main()

