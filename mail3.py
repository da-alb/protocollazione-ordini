import os
import email
import imaplib
from datetime import datetime
from email.utils import parseaddr
from extras import username_email
from extras import password_email
from extras import imap_server
from extras import get_customer_id
import re

base_dir = './allegati'

# Function to parse the store information from the subject line
def extract_store_info(subject):
    # Using regex to find the pattern "1O" or "1A"
    match = re.search(r'(\d+)[OA]', subject, re.IGNORECASE)
    if match:
        store_number = match.group(1)
        return f"store{store_number}"
    else:
        return 'unknown_store'

# Function to create the directory structure
def create_save_directory(base_dir, customer_id, store_name):
    # Get the current date
    today = datetime.today()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    day = today.strftime('%d')

    # Create the directory structure: year/month/day/customer-id/store
    save_dir = os.path.join(base_dir, year, month, day, customer_id, store_name)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    return save_dir

def get_unique_filename(directory, filename):
    """Generate a unique filename if the file already exists."""
    base, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_{counter}{extension}"
        counter += 1
    return new_filename

mail = imaplib.IMAP4_SSL(imap_server)

mail.login(username_email,password_email)

mail.select('INBOX')

status, messages = mail.search(None, '(UNSEEN)')

# If no new messages, exit
if status != 'OK' or not messages[0]:
    print("No unread messages found.")
    mail.logout()
    exit()

# Process each email
for num in messages[0].split():
    # Fetch the email by ID
    status, msg_data = mail.fetch(num, '(RFC822)')
    
    if status != 'OK':
        print(f"Failed to fetch email ID {num}")
        continue
    
    # Parse the email content
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            email_subject = msg['subject']
            email_from = msg['from']
            
            # Extract the actual email address
            actual_email = parseaddr(email_from)[1]
            print(f"Processing email from: {email_from}, Subject: {email_subject}")
            
            # Get the customer ID from the sender's email domain
            customer_id = get_customer_id(actual_email)
            
            # Define the store name (if it's fixed, you can set it here or extract from the email)
            store_name = 'store1'
            
            # Check for attachments
            for part in msg.walk():
                # If the part is multipart, skip
                if part.get_content_maintype() == 'multipart':
                    continue
                # If the part is not an attachment, skip
                if part.get('Content-Disposition') is None:
                    continue
                
                # Save the attachment
                file_name = part.get_filename()
                if file_name:
                    # Create the directory structure
                    save_dir = create_save_directory(base_dir, customer_id, store_name)
                    
                    # Generate a unique filename if a file with the same name already exists
                    unique_file_name = get_unique_filename(save_dir, file_name)
                    file_path = os.path.join(save_dir, unique_file_name)
                    
                    # Save the file
                    with open(file_path, 'wb') as file:
                        file.write(part.get_payload(decode=True))
                    print(f"Saved attachment: {file_path}")

# Logout from the mail server
mail.logout()
print("Done.")