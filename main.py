""" Process Framework. Attempt to emulate existing UiPath Framework """
"""NOTE FOR RCC USERS: Robocorp Lab and the Robocorp VS Code extension 
will pick up the devdata/env.json file automatically. While using RCC locally, you have 
to explicitly point to the file using the -e argument like so: rcc run -e devdata/env.json."""

# Standard RPA Libs
from RPA.HTTP import HTTP
from RPA.Robocorp.Vault import Vault
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.Dialogs import Dialogs
from RPA.Tables import Tables

# Standard lib
import json
import os
import logging
import sys

# Framework lib (custom errors and utilities)
from RobotSpareIndustries import RobotOrder


stdout = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    format='[{%(filename)s:%(lineno)s - %(message)s}]',
    handlers=[stdout],
)

LOGGER = logging.getLogger(__name__)

#workaround
def set_development_environment_variables():
    with open("./devdata/env.json") as env_in:
        env_file = json.load(env_in)
        for key in env_file:
            os.environ[key] = env_file[key]

def init_all_applications( config, _secrets):
    LOGGER.info('Opening all applications')

    if len(_secrets) == 0:
        url = 'https://robotsparebinindustries.com/#/robot-order'
    else:
        url = _secrets['robotspareindustries']['robot_order_url']

    robot_order = RobotOrder()
    robot_order.open_application(url)
    robot_order.accept_terms()

    return robot_order

def kill_all_applications( config ):
    print ('[Framework] Killing all applications')

def close_all_applications( config, robot_order ):
    LOGGER.info('Closing all applications')
    robot_order.close_application()


def get_transaction_data( config ):
    LOGGER.info('Fetching transaction data')
    http = HTTP()
    tables = Tables()


    http.download(url = 'https://robotsparebinindustries.com/orders.csv', target_file='data\orders.csv', overwrite=True)
    transaction_data = tables.read_table_from_csv('data\orders.csv', header = True, delimiters=',')
    return transaction_data

def get_transaction_item( config, transaction_data: Tables, transaction_number: int):
    LOGGER.info('Fetching next transaction')

    if transaction_number >= len( transaction_data ):
        return None
    
    return transaction_data[transaction_number]
    
def process( config, transaction_item, transaction_number, robot_order ):
    LOGGER.info(f'Processing transaction number: {transaction_number}')

    #Process variables
    folder_temp = os.path.join(os.path.curdir, 'temp')
    filename_temp_text = os.path.join(folder_temp, 'text{}.pdf'.format(transaction_number))
    filename_temp_image = os.path.join(folder_temp, 'image{}.png'.format(transaction_number))
    filename_output = os.path.join(os.path.curdir, 'output', 'receipts', 'output{}.pdf'.format(transaction_number))
    pdf = PDF()


    robot_order.new_order(str(transaction_item[1]), 
                            str(transaction_item[2]), 
                            str(transaction_item[3]), 
                            str(transaction_item[4]))
    robot_order.preview()
    robot_order.order()
    receipt = robot_order.get_receipt_as_html()
    pdf.html_to_pdf(receipt, filename_temp_text)
    robot_order.download_robot_preview(filename_temp_image)
    pdf.add_files_to_pdf(files = [filename_temp_text, filename_temp_image], 
                         target_document = filename_output)

    robot_order.order_another_robot()
    robot_order.accept_terms()
    
    for f in os.listdir(folder_temp):
        file_to_remove = os.path.join(folder_temp, f)
        try:
            os.unlink(file_to_remove)
        except Exception as e:
            print(f'Failed to remove {f}. Reason: {str(e)}')

    

def init_all_settings():
    LOGGER.info('Initializing settings')
    config = {}
    _secrets = []

    with open("Data\config.json", 'r') as f:
        local_config = json.load(f)

    for k,v in local_config['settings'].items():
        config[k] = v
    for k,v in local_config['framework'].items():
        config[k] = v

    try:
        for s in local_config['secrets']:
            secret = Vault().get_secret(s)
            _secrets.append(secret)
    except Exception as e:
        LOGGER.exception(f'Failed to fetch secrets: {str(e)}')

    return config, _secrets

def get_user_input():
    try:
        dialogs = Dialogs()
        dialogs.add_text("What do you want to call the output?")
        dialogs.add_text_input(name='file_name', label='Output name')
        user_input = dialogs.run_dialog(title='Provide a name for the output plz', width=400, height=500)
    except Exception as e:
        LOGGER.exception('Unable to get user input, setting it to default. Reason: ' + str(e))
        user_input = {
            "file_name" : "default"
        }
    finally:
        dialogs.close_all_dialogs()
        return user_input


if __name__ == "__main__":
    set_development_environment_variables()
    config, _secrets = init_all_settings()
    LOGGER.info('Starting')
    
    # Set global variables
    config = {}
    transaction_number = 0
    transactions_remain = True
    max_retries = 0
    retry_number = 0
    restart_needed = False

    # Declare all windows / Systems in scope.
    robot_order = None

    # GET USER INPUT
    user_input = get_user_input()

    # INIT 
    #config, _secrets = init_all_settings()
    robot_order = init_all_applications( config, _secrets ) # Returns all application objects
    transaction_data = get_transaction_data( config )

    while transactions_remain:
        
        # GET TRANSACTION ITEMS
        try:
            transaction_item = get_transaction_item(config, transaction_data, transaction_number)
        except Exception as e:
            LOGGER.exception('Failed to get transaction item: ' + str(e))
            transaction_number += 1
            continue
        
        if transaction_item == None:
            break

        if restart_needed:
            robot_order = init_all_applications( config, _secrets )

        # PROCESS TRANSACTION
        try:
            process( config, transaction_item, transaction_number, robot_order )
            restart_needed = False
            transaction_number += 1

        except Exception as e:
            LOGGER.exception('Transaction Exception: ' + str(e))
            try:
                close_all_applications( config, robot_order )
            except Exception:
                LOGGER.exception('Failed to close all applications: ' + str(e) )
                kill_all_applications( config )
            finally:
                restart_needed = True
                retry_number += 1
                if retry_number < max_retries:
                    LOGGER.info('Retrying transaction')
                else:
                    transaction_number += 1

    
    # WRAP UP / TEARDOWN
    try:
        close_all_applications( config, robot_order )
    except Exception as e:
        LOGGER.exception('Failed to close all applications: ' + str(e) )
        kill_all_applications( config )


    try: 
        archive = Archive()
        archive.archive_folder_with_zip(os.path.join(os.path.curdir, 'output', 'receipts'), 
                                        os.path.join(os.path.curdir, 'output', user_input['file_name'] + '.zip'))
    except Exception as e:
        LOGGER.exception(f'Failed to archive receipts: {str(e)}')
    
    finally:
        for f in os.listdir(os.path.join(os.path.curdir, 'output', 'receipts')):
            file_to_remove = os.path.join(os.path.join(os.path.curdir, 'output', 'receipts'), f)
            try:
                os.unlink(file_to_remove)
            except Exception as e:
                print(f'Failed to remove {f}. Reason: {str(e)}')


#TODO
#   x paths as variables in config
#   x path separator ( / or \)
#   x zip output
#   - HANDLE CRASCH BETTER
#   x use logging instead of print
#   X open assistant for file save/ url of the csv
#   - use the Vault somehow, order robot website for example.