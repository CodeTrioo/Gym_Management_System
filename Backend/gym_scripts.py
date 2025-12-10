import os
import django
from getpass import getpass

# ------------------------------
# Load Django settings
# ------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from accounts.models import Member
from django.contrib.auth.models import User

# ------------------------------
# Functions
# ------------------------------
def add_member():
    username = input("Enter username: ").strip()
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists!")
        return
    password = getpass("Enter password: ").strip()
    age = input("Enter age: ").strip()
    membership_type = input("Enter membership type: ").strip()

    user = User.objects.create_user(username=username, password=password)
    Member.objects.create(user=user, age=int(age), membership_type=membership_type)
    print(f"Member '{username}' added successfully!")

def edit_member():
    username = input("Enter username to edit: ").strip()
    try:
        member = Member.objects.get(user__username=username)
        print("Leave blank to keep current value.")
        new_age = input(f"Current age: {member.age}, New age: ").strip()
        new_membership = input(f"Current membership: {member.membership_type}, New membership: ").strip()
        if new_age:
            member.age = int(new_age)
        if new_membership:
            member.membership_type = new_membership
        member.save()
        print(f"Member '{username}' updated successfully!")
    except Member.DoesNotExist:
        print(f"Member '{username}' not found!")

def delete_member():
    username = input("Enter username to delete: ").strip()
    confirm = input(f"Are you sure you want to delete '{username}'? [yes/no]: ").strip().lower()
    if confirm != "yes":
        print("Delete cancelled.")
        return
    try:
        user = User.objects.get(username=username)
        user.delete()
        print(f"Member '{username}' deleted successfully!")
    except User.DoesNotExist:
        print(f"Member '{username}' not found!")

def list_members():
    members = Member.objects.all()
    if not members:
        print("No members found.")
        return
    print("\nAll Gym Members:")
    for m in members:
        print(f"- {m.user.username}, Age: {m.age}, Membership: {m.membership_type}, Joined: {m.join_date}")
    print("")

# ------------------------------
# Menu
# ------------------------------
def main():
    while True:
        print("\nGym Management System")
        print("1. Add Member")
        print("2. Edit Member")
        print("3. Delete Member")
        print("4. List Members")
        print("5. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            add_member()
        elif choice == "2":
            edit_member()
        elif choice == "3":
            delete_member()
        elif choice == "4":
            list_members()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
