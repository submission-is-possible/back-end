from django.core.mail import EmailMultiAlternatives

def send_reviewer_acceptance_email(admin_user, reviewer_user, conference_title):
    subject = f'Reviewer Acceptance for the conference "{conference_title}"'
    from_email = 'submissionispossible6@gmail.com'
    text_content = f'{reviewer_user.first_name} {reviewer_user.last_name} has accepted the invitation to be a reviewer for the conference "{conference_title}".'

    email_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #F2E3EB;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                padding: 10px 0;
                background-color: #873F7E;
                color: #fff;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                padding: 20px;
            }}
            .button {{
                display: block;
                width: 200px;
                margin: 20px auto;
                padding: 10px;
                text-align: center;
                background-color: #D7AEEE;
                color: #333;
                text-decoration: underline;
                border-radius: 5px;
                border: 1px solid #D7AEEE;
            }}
            .button:hover {{
                background-color: #ffcccc;
                border-color: #ffcccc;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Reviewer Acceptance Notification</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>{reviewer_user.first_name} {reviewer_user.last_name} has accepted the invitation to be a reviewer for the conference "<strong>{conference_title}</strong>".</p>
                <p>For more information, please visit our website: </p>
                <a href="http://http://localhost:5173/login" class="button">Go to SubmissionIsPossible</a>
                <p>Thank you,</p>
                <p>The SubmissionIsPossible Team</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [admin_user.email])
    msg.attach_alternative(email_content, "text/html")
    msg.send()
