import pickle
from collections import UserDict
from datetime import datetime, timedelta


DATE_PATTERN = "%d.%m.%Y"


def save_data(book, filename="book.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="book.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


class RequiredFieldError(Exception):
    pass


class FieldFormatError(Exception):
    pass


def error_handler(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)        
        except (RequiredFieldError, FieldFormatError) as e:
            print(f"[ERROR] Validation failed: {e}")        
        except ValueError:            
            print("Phone number not found.")
        except KeyError:            
            print("Contact not found.")
        except Exception as e:
            print(f"[ERROR] Unknown exception: {e}")

    return inner


class Field:
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value: str):
        if len(value.strip()) == 0:
            raise RequiredFieldError("Required not empty field.")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value: str):
        if len(value) != 10 or not all(c.isdigit() for c in value):
            raise FieldFormatError("Must be exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str):
        try:
            datetime.strptime(value, "%d.%m.%Y")            
        except ValueError:
            raise FieldFormatError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)

class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
    
    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"

    @error_handler
    def add_phone(self, phone_number: str):
        phone = Phone(phone_number)
        if phone and phone not in self.phones:
            self.phones.append(Phone(phone_number))
    
    @error_handler
    def remove_phone(self, phone_number: str):
        index = self.__get_phone_index(phone_number)
        if index >= 0:
            return self.phones.pop()

    @error_handler
    def edit_phone(self, old_phone_number: str, new_phone_number: str):
        index = self.__get_phone_index(old_phone_number)
        if index >= 0:
            new_phone = Phone(new_phone_number)
            if new_phone:
                self.phones[index] = new_phone

    @error_handler    
    def find_phone(self, phone_number: str):    
        index = self.__get_phone_index(phone_number)
        if index >= 0:        
            return self.phones[index]

    def __get_phone_index(self, phone_number: str):
        for index in range(0, len(self.phones)):
            if self.phones[index].value == phone_number:
                return index
        raise ValueError
    
    def phones_info(self):
        return ', '.join(p.value for p in self.phones)

    @error_handler
    def add_birthday(self, day: str):
        birthday = Birthday(day)
        if birthday:
            self.birthday = birthday

    def birthday_info(self):
        return f"{self.name.value} was born in {self.birthday.value if self.birthday else 'N/A'}"


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record
        return self.data[record.name.value]

    @error_handler
    def find(self, name):
        return self.data[name]
    
    @error_handler
    def delete(self, name):
        self.data.pop(name)

    def get_upcoming_birthdays(self):
        greetings_list = []

        current_date = datetime.today().date()
        current_year = current_date.year

        for record in self.data.values():
            if not record.birthday:
                continue

            user_born_date = datetime.strptime(record.birthday.value, DATE_PATTERN).date()
            birthday = datetime(current_year, user_born_date.month, user_born_date.day).date()

            delta_days = (birthday - current_date).days
            is_upcoming = delta_days >= 0 and delta_days <= 7

            if is_upcoming:
                extra_days = 0 if birthday.weekday() < 5 else (7 - birthday.weekday())
                greetings_date = birthday + timedelta(extra_days)
                user_greeting_data = {
                    "name": record.name.value, 
                    "congratulation_date": datetime.strftime(greetings_date, DATE_PATTERN)
                }
                greetings_list.append(user_greeting_data)
            
        return greetings_list


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()    
    return cmd, *args


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            print(f"[ERROR] Data inconsistency: {e}")
        except ValueError as e:            
            print(f"[ERROR] Unsupported format: {e}")
        except IndexError as e:
            print(f"[ERROR] Arguments mismatch: {e}")

    return inner


def validate_arguments(args, expected):
    if len(args) != expected:
        raise IndexError(f"Arguments: expected='1', provided='{len(args)}'.")


def validate_phone(value):
    if len(value) != 10 or not all(c.isdigit() for c in value):
        raise ValueError(f"Phone number format 10 digits: expected='XXXXXXXXXX', provided='{value}'.")
    

def validate_date(value):
    try:
        datetime.strptime(value, DATE_PATTERN)
    except ValueError:
        raise ValueError(f"Birthday date format is incorrect: expected='DD.MM.YYYY', provided='{value}'.")
        

def validate_contact(name, names):    
    if name not in names:        
        raise KeyError(f"Contact with name '{name}' does not exist.")
    

@input_error
def add_contact(args, book: AddressBook):
    validate_arguments(args, 2)
    name, phone = args
    validate_phone(phone)

    record: Record = book.get(name) if book.get(name) else Record(name)
    record.add_phone(phone)

    book.add_record(record)
    print("Contact added.")


@input_error
def change_contact(args, book: AddressBook):
    validate_arguments(args, 3)
    
    name, old_phone, new_phone = args

    validate_contact(name, book.data.keys())
    validate_phone(old_phone)
    validate_phone(new_phone)

    record: Record = book[name]
    record.edit_phone(old_phone, new_phone)      
    print("Contact updated.")


@input_error
def show_phone(args, book: AddressBook):
    validate_arguments(args, 1)
    
    name, = args
    validate_contact(name, book.data.keys())
    print(f"Phones: {book.get(name).phones_list()}")


@input_error
def add_birthday(args, book: AddressBook):
    validate_arguments(args, 2)
    
    name, date = args
    validate_contact(name, book.data.keys())
    validate_date(date)

    record: Record = book[name]
    record.add_birthday(date)      
    print("Contact updated.")


@input_error
def show_birthday(args, book: AddressBook):
    validate_arguments(args, 1)
    
    name, = args
    validate_contact(name, book.data.keys())
    
    record: Record = book[name]    
    print(record.birthday_info())


def show_all(book: AddressBook):
    if not book.values():
        print("There are no contacts.")
        return
    
    size = max(len(record.phones_info()) for record in book.values()) + 4
    dash_row = "-" * (size * 2 + 1)
    header = [dash_row, f"{'NAME':^{size}}|{'PHONE':^{size}}", dash_row]
    contacts_list = header + [f"{contact.name.value:<{size}}|{contact.phones_info():^{size}}" for contact in book.values()]    
    
    print("\n".join(contacts_list))


def show_upcoming_bitrhdays(book: AddressBook):
    info = book.get_upcoming_birthdays()
    for item in info:
        print(f"Name: {item['name']}, Birthday: {item['congratulation_date']}")


def main():
    address_book = load_data()
    print("Welcome to the assistant bot!")
            
    while True:
        save_changes = False
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        match command:
            case "add":
                add_contact(args, address_book)
                save_changes = True

            case "change":
                change_contact(args, address_book)
                save_changes = True

            case "phone":
                show_phone(args, address_book)

            case "all":
                show_all(address_book)

            case "birthdays":
                show_upcoming_bitrhdays(address_book)

            case "add-birthday":
                add_birthday(args, address_book)
                save_changes = True
            
            case "show-birthday":
                show_birthday(args, address_book)
            
            case "hello":
                print("How can I help you?")

            case "close" | "exit":
                save_data(address_book)
                print("Good bye!")
                break

            case _:
                print("Invalid command.")

        if save_changes:
            save_data(address_book)


if __name__ == "__main__":
    main()
