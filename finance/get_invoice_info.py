import requests
from datetime import datetime
import os
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Configuration
BASE_URL = "https://api.linode.com/v4/"
HEADERS = {
    "Authorization": f"Bearer {os.environ.get('LINODE_API_TOKEN')}",
    "Content-Type": "application/json"
}
SMTP_CONFIG = {
    "server": os.environ.get('SMTP_SERVER'),
    "port": int(os.environ.get('SMTP_PORT')),
    "username": os.environ.get('SMTP_USERNAME'),
    "password": os.environ.get('SMTP_PASSWORD')
}
EMAIL_CONFIG = {
    "from": os.environ.get('EMAIL_FROM'),
    "recipients": os.environ.get('RECIPIENTS').split(","),
    "subject": os.environ.get('EMAIL_SUBJECT', 'Linode Monthly Report') 
}
OUTPUT_PATH = os.environ.get('OUTPUT_PATH')


def get_filename(base_name):
    return os.path.join(OUTPUT_PATH, f"{base_name}-{datetime.now().strftime('%Y-%m-%d')}.png")


def request_data(endpoint):
    response = requests.get(BASE_URL + endpoint, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from {endpoint}: {response.text}")
        return None


def get_account_info():
    return request_data("account")


def get_all_invoices():
    invoices = []
    page = 1
    while True:
        data = request_data(f"account/invoices?page={page}")
        if 'data' in data:
            invoices.extend(data['data'])

            # Handle pagination
            if data['page'] < data['pages']:
                page += 1
            else:
                break
        else:
            break
    return invoices


def calculate_invoice_totals(invoices):
    now = datetime.now()
    start_of_current_month = datetime(now.year, now.month, 1)
    start_of_year = datetime(now.year, 1, 1)
    start_of_last_month = datetime(now.year - (now.month == 1), (now.month - 1) or 12, 1)

    last_month_invoices = [i for i in invoices if start_of_last_month <= datetime.fromisoformat(i['date']) < start_of_current_month]
    current_month_invoices = [i for i in invoices if start_of_current_month <= datetime.fromisoformat(i['date']) <= now]
    year_to_date_invoices = [i for i in invoices if start_of_year <= datetime.fromisoformat(i['date']) <= now]

    return {
        "Last Month Total": sum(i['total'] for i in last_month_invoices),
        "Current Month Total": sum(i['total'] for i in current_month_invoices),
        "Year to Date Total": sum(i['total'] for i in year_to_date_invoices)
    }


def plot_chart(title, labels, values, colors, filename):
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color=colors)
    plt.title(title)
    plt.ylabel("Amount ($)")

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 100, round(yval, 2), ha='center', va='bottom')

    plt.savefig(filename)
    plt.show()


def display_summary(account_summary, invoice_totals):
    # Print Account Summary and Invoice Totals
    print("\n----- Account Summary -----")
    for key, value in account_summary.items():
        print(f"{key}: ${value:.2f}" if isinstance(value, (int, float)) else f"{key}: {value}")
    print("---------------------------")

    print("\n----- Invoice Totals -----")
    for key, value in invoice_totals.items():
        print(f"{key}: ${value:.2f}")
    print("---------------------------")

    # Plotting charts
    if 'active_promotions' in account_summary and account_summary['active_promotions']:
        promotion = account_summary['active_promotions'][0]
        credit_labels = ['Credit Remaining', 'Credit Monthly Cap']
        credit_values = [float(promotion['credit_remaining']), float(promotion['credit_monthly_cap'])]
        plot_chart("Credit Overview", credit_labels, credit_values, ['#56B4E9', '#D55E00'], get_filename("credit_overview"))

    if 'balance_uninvoiced' in account_summary:
        plot_chart("Accrued Charges Overview", ['Accrued Charges Since Last Month'], [account_summary['balance_uninvoiced']], ['#009E73'], get_filename("accrued_charges_overview"))

def format_account_summary(account_summary):
    formatted_summary = "----- Account Summary -----\n\n"
    
    # Select and format the main details
    details = {
        'company': account_summary['company'],
        'email': account_summary['email'],
        'balance': f"${account_summary['balance']:.2f}",
        'credit used': f"${account_summary['balance_uninvoiced']:.2f}",
        'active_since': account_summary['active_since']
    }
    formatted_summary += "\n".join([f"{key}: {value}" for key, value in details.items()])

    # Extract and format active promotions if they exist
    if 'active_promotions' in account_summary and account_summary['active_promotions']:
        promotion = account_summary['active_promotions'][0]  # assuming you want the first promotion
        formatted_summary += f"\n{promotion['summary']}"
        formatted_summary += f"\n  - expiration: {promotion['expire_dt']}"
        formatted_summary += f"\n  - credit monthly cap: ${promotion['credit_monthly_cap']}"
        formatted_summary += f"\n  - credit remaining: ${promotion['credit_remaining']}"
        formatted_summary += f"\n  - credit remaining this month: ${promotion['this_month_credit_remaining']}"

    return formatted_summary + "\n---------------------------\n\n"


def format_invoice_totals(invoice_totals):
    formatted_invoice_totals = "----- Invoice Totals -----\n\n"
    formatted_invoice_totals += "\n".join([f"{key}: ${value:.2f}" for key, value in invoice_totals.items()])
    return formatted_invoice_totals + "\n---------------------------\n\n"


def send_email(to_addresses, subject, body, attachments=[]):
    with smtplib.SMTP_SSL(SMTP_CONFIG["server"], SMTP_CONFIG["port"]) as server:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["from"]
        msg['To'] = ', '.join(to_addresses)
        msg['Subject'] = EMAIL_CONFIG["subject"]
        msg.attach(MIMEText(body, 'plain'))

        for attachment in attachments:
            if os.path.exists(attachment):
                with open(attachment, "rb") as file:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment)}")
                    msg.attach(part)

        server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
        server.sendmail(EMAIL_CONFIG["from"], to_addresses, msg.as_string())


if __name__ == "__main__":
    account_summary = get_account_info()
    invoice_totals = calculate_invoice_totals(get_all_invoices())
    display_summary(account_summary, invoice_totals)
    email_body = format_account_summary(account_summary) + format_invoice_totals(invoice_totals)
    send_email(EMAIL_CONFIG["recipients"], 'Monthly Report', email_body, [get_filename("credit_overview"), get_filename("accrued_charges_overview")])
