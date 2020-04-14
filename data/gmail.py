import pickle, os, base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors
from tqdm import tqdm

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def service(credentials="credentials.json"):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

def search(service, query, user_id="me"):
    try:
        response = service.users().messages().list(userId="me", q=query).execute()
        messages = []

        if "messages" in response:
            messages.extend(response["messages"])

        while "nextPageToken" in response:
            page_token = response["nextPageToken"]
            response = service.users().messages().list(
                userId=user_id, q=query, pageToken=page_token).execute()
            messages.extend(response["messages"])

        return messages
    except errors.HttpError as error:
        print("An error occurred: {}".format(error))

def get(service, msg_id, user_id="me", output="raw"):
    try:
        message = service.users().messages().get(
            userId=user_id, id=msg_id, format=output).execute()

        return base64.urlsafe_b64decode(message[output].encode("ASCII"))
    except errors.HttpError as error:
        print("An error occurred: {}".format(error))

def download(service, query, user_id="me", output="raw", offset=0):
    for res in tqdm(search(service, query, user_id)[offset:]):
        open(os.path.join(output, res["id"] + ".eml"), "wb+").write(
            get(service, res["id"], user_id))

if __name__ == "__main__":
    import argparse
    relpath = lambda *args: os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)
    parser = argparse.ArgumentParser(description="Download gmail search results")
    parser.add_argument("--output", default=relpath("raw"))
    parser.add_argument("--credentials", default=relpath("credentials.json"))
    parser.add_argument("--offset", type=int, default=0)
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--no-overwrite", dest="overwrite", action="store_const", const=0)
    group.add_argument("--overwrite", dest="overwrite", action="store_const", const=1)
    group.add_argument("--ask-overwrite", dest="overwrite", action="store_const", const=2)
    parser.set_defaults(overwrite=2)
    parser.add_argument("query", type=str, nargs=1)
    args = parser.parse_args()

    if os.path.exists(args.output):
        if args.overwrite == 2:
            while True:
                overwrite = input('Overwrite contents of "{}"? [yN] '.format(args.output))
                if overwrite == "" or overwrite.lower() == "n":
                    args.overwrite = 0
                elif overwrite.lower() == "y":
                    args.overwrite = 1
                else:
                    overwrite = input('Please enter "y" or "n" (nothing defaults to n) ")')
                    continue
                break

        if args.overwrite:
            shutil.rmtree(args.output, True)
            os.mkdir(args.output)
    else:
        os.mkdir(args.output)

    download(service(args.credentials), args.query, output=args.output, offset=args.offset)
