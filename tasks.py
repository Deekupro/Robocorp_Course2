from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
import time


@task
def order_robots_from_RobotSpareBin():
    browser.configure(slowmo=100)
    open_robotspareindustries()
    get_orders_csv_file()
    csv_content = get_orders()
    create_orders(csv_content)
    archive_receipts()


def get_orders_csv_file():
    """Download the csv file used in creating orders"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

def get_orders():
    """Read CSV table"""
    tables = Tables()
    csv_content = tables.read_table_from_csv(path="orders.csv", header=True)
    return csv_content

def close_annnoying_modal():
    """Press 'I guess so...' on popup"""
    page = browser.page()
    page.click("//*[text()='I guess so...']")

def open_robotspareindustries():
    """Open robotsparebin industries website"""
    page = browser.page()
    page.goto(url="https://robotsparebinindustries.com/#/robot-order")

def create_orders(csv_content):
    """Loop through every row and get all nessecary data from the website."""
    page = browser.page()
    for row in csv_content:
        close_annnoying_modal()
        fill_the_form(row)

def fill_the_form(row):
    page = browser.page()
    
    """Input data from CSV"""
    page.select_option("//select[@id='head']", value=row["Head"])
    page.click("//input[@type='radio' and @value='" + row["Body"] + "']")
    page.fill("//label[text()='3. Legs:']/following-sibling::input", value=row["Legs"])
    page.fill("//input[@name='address']", value=row["Address"])

    """Automation clicks Order button until it is succesfully pressed."""
    while True:
        page.click("//button[@id='order']")
        if page.query_selector("//button[text()='Order another robot']"):
            time.sleep(0.5)
            receipt_filepath = store_receipt_as_pdf(row["Order number"])
            screenshot_filepath = screenshot_robot(row["Order number"])
            embed_screenshot_to_receipt(screenshot_filepath, receipt_filepath)
            page.click("//button[text()='Order another robot']")
            break
    return receipt_filepath


def store_receipt_as_pdf(order_number):
    """Save receipt as a PDF file to receipts folder"""
    page = browser.page()
    pdf = PDF()
    receipt_filepath = "output/receipts/receipt_" + order_number + ".pdf"

    receipt = page.locator("//div[@id='receipt']").inner_html()
    pdf.html_to_pdf(receipt, receipt_filepath)

    return receipt_filepath

def screenshot_robot(order_number):
    """Save screenshot as a png to screenshots folder"""
    page = browser.page()
    screenshot_filepath = "output/screenshots/robot_" + order_number + ".png"

    robot_img = page.locator("//div[@id='robot-preview-image']")
    robot_img.screenshot(path=screenshot_filepath)

    return screenshot_filepath

def embed_screenshot_to_receipt(screenshot_filepath, receipt_filepath):
    """Add screenshot of the robot to the existing receipt PDF"""
    pdf = PDF()
    file_to_append=[screenshot_filepath]

    pdf.add_files_to_pdf(file_to_append, receipt_filepath, True)

def archive_receipts():
    """Archive receipt folder contents"""
    archive = Archive()

    archive.archive_folder_with_zip(folder="output/receipts/", archive_name="output/receipts_as_zip.zip")