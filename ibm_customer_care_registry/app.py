from flask import Flask, render_template, request, redirect, url_for, session,flash
import ibm_db
from datetime import date
import pandas as pd
import smtplib
import ssl
from email.message import EmailMessage
import json
import requests

app = Flask(__name__)
app.secret_key="hello"
conn = ibm_db.connect(
    "DATABASE=bludb;HOSTNAME=ea286ace-86c7-4d5b-8580-3fbfa46b1c66.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31505;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=ksm14837;PWD=ueHJCZVCFdme95eQ",
    '', '')

def sendmail(subject,receiver,body):
    email_sender='complaintcare511@gmail.com'
    email_password='pvpszmhsdesatrpp'
    msg=EmailMessage()
    msg['Subject']=subject
    msg['From']=email_sender
    msg['To']=receiver
    msg.set_content(body)
    with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
        smtp.login(email_sender,email_password)
        smtp.send_message(msg)




@app.route('/registration')
def homepage():
    return render_template('register.html')

@app.route('/register',methods=['POST'])
def register():
    if "user" in session:
        return redirect(url_for('uhome'))
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    sql = "SELECT * FROM USERS WHERE email =?"
    stmt = ibm_db.prepare(conn, sql)

    ibm_db.bind_param(stmt, 1, email)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    print(account)
    if account:
        flash("You are already a member, please login using your details")
        return render_template('register.html')
    else:
        insert_sql = "INSERT INTO USERS VALUES (?, ?, ?, ?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, name)
        ibm_db.bind_param(prep_stmt, 2, email)
        ibm_db.bind_param(prep_stmt, 3, phone)
        ibm_db.bind_param(prep_stmt, 4, password)
        ibm_db.execute(prep_stmt)
        flash("Registration Successful, please login using your details")
        return render_template('register.html')

@app.route('/')
@app.route('/login')
def login():
    if "user" in session:
        return redirect(url_for('uhome'))
    return render_template('login.html')


@app.route('/loginpage', methods=['POST'])
def loginpage():
    user = request.form['email']
    passw = request.form['password']
    sql = "SELECT * FROM USERS WHERE email =? AND password=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, user)
    ibm_db.bind_param(stmt, 2, passw)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    print(account)
    print(user, passw)
    if account:
        session['user']=user
        session['name']=account['NAME']
        return redirect(url_for('uhome'))
    else:
        flash("Login unsuccessful. Incorrect username / password !")
        return render_template('login.html',)

@app.route("/profile")
def profile():
    if 'user' in session:
        email=session['user']
        sql = "SELECT * FROM USERS WHERE email =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        return render_template('profile.html',name=account['NAME'],email=email,phone=account['PHONE'],user=session['name'])
    else:
        return redirect(url_for('login'))


@app.route("/uhome")
def uhome():
    if 'user' in session:
        user=session['user']
        username=session['name']
        sql1 = "SELECT COUNT(*) AS C1 FROM  COMPLAINTS WHERE C_STATUS=? AND U_EMAIL=? "
        stmt = ibm_db.prepare(conn, sql1)
        ibm_db.bind_param(stmt, 1, "UNADDRESSED")
        ibm_db.bind_param(stmt, 2, user)
        ibm_db.execute(stmt)
        unaddressed = ibm_db.fetch_assoc(stmt)
        print(unaddressed)
        sql2 = "SELECT COUNT(*) AS C2 FROM  COMPLAINTS WHERE C_STATUS=? AND U_EMAIL=?"
        stmt = ibm_db.prepare(conn, sql2)
        ibm_db.bind_param(stmt, 1, "ADDRESSED")
        ibm_db.bind_param(stmt, 2, user)
        ibm_db.execute(stmt)
        addressed = ibm_db.fetch_assoc(stmt)
        print(addressed)
        sql3 = "SELECT COUNT(*) AS C3 FROM  COMPLAINTS WHERE C_STATUS=? AND U_EMAIL=?"
        stmt = ibm_db.prepare(conn, sql3)
        ibm_db.bind_param(stmt, 1, "COMPLETED")
        ibm_db.bind_param(stmt,2,user)
        ibm_db.execute(stmt)
        completed = ibm_db.fetch_assoc(stmt)
        print(completed)
        return render_template('uhome.html',user=username,ac=unaddressed['C1']+addressed['C2'],c=completed['C3'])
    else:
        return redirect(url_for('login'))

@app.route("/complaint")
def complaint():
    if "user" in session:
        return render_template('complaint.html',user=session['name'])
    else:
        return redirect(url_for('login'))
@app.route('/complaintpage', methods=['POST'])
def complaintpage():
    complaint =request.form["comp"]
    email = session['user']
    Date=date.today()
    sql = "INSERT INTO COMPLAINTS(U_EMAIL, COMPLAINT,C_STATUS,DATE) VALUES (?,?,?,?)"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, email)
    ibm_db.bind_param(stmt, 2, complaint)
    ibm_db.bind_param(stmt, 3, "UNADDRESSED")
    ibm_db.bind_param(stmt, 4, Date)
    ibm_db.execute(stmt)
    sql = "SELECT COMPLAINT_ID  FROM COMPLAINTS WHERE U_EMAIL=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, email)
    ibm_db.execute(stmt)
    account=ibm_db.fetch_assoc(stmt)
    cid=account['COMPLAINT_ID']
    subject="Complaint Registration"
    body=f"Your complaid with ID-{cid}has been successfully registered.An Agent will been assigned as soon as possible"
    try:
        sendmail(subject=subject,receiver=email,body=body)
    except:
        pass
    return render_template( "complaint.html",pred="Complaint Raised Successfully!!",user=session['name'])
@app.route('/checkstatus')
def checkstatus():
    if 'user' in session:
        email=session['user']
        sql = "SELECT COMPLAINT_ID,C_STATUS FROM COMPLAINTS WHERE U_EMAIL =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        hist=[]
        while account != False:
            hist.append(account)
            account = ibm_db.fetch_assoc(stmt)
        print(hist)
        df = pd.json_normalize(hist)
        print(df)
        df.index = df.index + 1

        print(account)
        return render_template('u_status.html', tables=[df.to_html()], titles=[''],user=session['name'])
    else:
        return redirect(url_for('login'))



@app.route('/admin')
def admin():
    if "aemail" in session:
        return redirect(url_for('ahome'))
    return render_template('admin.html')


@app.route('/adminpage', methods=['POST'])
def adminpage():
    user = request.form['email']
    passw = request.form['password']
    sql = "SELECT * FROM ADMIN WHERE email =? AND password=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, user)
    ibm_db.bind_param(stmt, 2, passw)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    print(account)
    print(user, passw)
    if account:
        session['aemail']=user
        session['aname']=account['NAME']
        return redirect(url_for('ahome'))
    else:
        flash("Login unsuccessful. Incorrect credentials !")
        return render_template('admin.html')

@app.route('/ahome')
def ahome():
    if 'aemail' in session:
        name=session['aname']
        sql1 = "SELECT COUNT(*) AS C1 FROM  COMPLAINTS WHERE C_STATUS=? "
        stmt = ibm_db.prepare(conn, sql1)
        ibm_db.bind_param(stmt, 1, "UNADDRESSED")
        ibm_db.execute(stmt)
        unaddressed= ibm_db.fetch_assoc(stmt)
        print(unaddressed)
        sql2 = "SELECT COUNT(*) AS C2 FROM  COMPLAINTS WHERE C_STATUS=? "
        stmt = ibm_db.prepare(conn, sql2)
        ibm_db.bind_param(stmt, 1, "ADDRESSED")
        ibm_db.execute(stmt)
        addressed= ibm_db.fetch_assoc(stmt)
        print(addressed)
        sql3 = "SELECT COUNT(*) AS C3 FROM  COMPLAINTS WHERE C_STATUS=? "
        stmt = ibm_db.prepare(conn, sql3)
        ibm_db.bind_param(stmt, 1, "COMPLETED")
        ibm_db.execute(stmt)
        completed = ibm_db.fetch_assoc(stmt)
        print(completed)
        return render_template('ahome.html',admin=name,ua=unaddressed['C1'],a=addressed['C2'],c=completed['C3'])
    else:
        return redirect(url_for('admin'))

@app.route('/viewcomplaints')
def viewcomplaints():
    if 'aemail' in session:
        return render_template('viewcomplaints.html',admin=session['aname'])
    else:
        return redirect(url_for('admin'))

@app.route('/vcomplaint',methods=['POST'])
def vcomplaint():
    email = session['aemail']
    status=request.form["status"]
    sql = "SELECT DATE,COMPLAINT_ID,COMPLAINT,C_STATUS,U_EMAIL FROM COMPLAINTS WHERE C_STATUS=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, status)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    hist = []
    while account != False:
        hist.append(account)
        account = ibm_db.fetch_assoc(stmt)
    print(hist)
    if hist:
        df1 = pd.json_normalize(hist)
        print(df1)
        df1.index = df1.index + 1
        records1 = df1.to_records(index=False)
        hists=list(records1)

        print(account)
        return render_template('viewcomplaints.html',admin=session['aname'],data=hists)
    else:
        return render_template('viewcomplaints.html', pred="No complaints to view",admin=session['aname'])

@app.route('/assignagent')
def assignagent(pred=''):
    if 'aemail' in session:
        sql = "SELECT * FROM AGENTS"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        hist = []
        while account != False:
            hist.append(account['AGENTID'])
            account = ibm_db.fetch_assoc(stmt)
        return render_template('assignagents.html',x=hist,pred=pred,admin=session['aname'])
    else:
        return redirect(url_for('admin'))

@app.route('/agents',methods=['POST'])
def agents():
    c_id= request.form['c_id']
    agent = request.form['agent']
    sql = "SELECT COMPLAINT,U_EMAIL,AGENT FROM COMPLAINTS WHERE COMPLAINT_ID=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, c_id)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_both(stmt)
    if account:
        if account['AGENT']:
            return assignagent(pred='Agent Already Assigned')
        else:
            sql = "UPDATE COMPLAINTS SET AGENT=?,C_STATUS=? WHERE COMPLAINT_ID =? AND C_STATUS=?"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt, 1, agent)
            ibm_db.bind_param(stmt, 2, "ADDRESSED")
            ibm_db.bind_param(stmt, 3, c_id)
            ibm_db.bind_param(stmt, 4, "UNADDRESSED")
            ibm_db.execute(stmt)
            email=account['U_EMAIL']
            cid = c_id
            subject = "Assigned to Agent"
            body = f"Your complaid with ID-{cid} has been assigned to agent."
            try:
                sendmail(subject=subject, receiver=email, body=body)
            except:
                pass
            return assignagent( pred="Agent assigned successfully!")
    else:
        return assignagent(pred="Agent not assigned! check complaint id ")

@app.route('/acheckstatus')
def acheckstatus():
    if 'aemail' in session:
        return render_template('admincheckstatus.html',admin=session['aname'])
    else:
        return redirect(url_for('admin'))

@app.route('/astatuspage',methods=['POST'])
def astatuspage():
    cid=request.form['cid']
    sql='SELECT * FROM COMPLAINTS WHERE COMPLAINT_ID=?'
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,cid)
    ibm_db.execute(stmt)
    account=ibm_db.fetch_assoc(stmt)
    if account:
        return render_template('admincheckstatus.html',pred2=account['C_STATUS'],admin=session['aname'])
    else:
        return render_template('admincheckstatus.html',pred2='check complaint id',admin=session['aname'])



@app.route('/createagent')
def createagent():
    if 'aemail' in session:
        return render_template('createagent.html',admin=session['aname'])
    else:
        return redirect(url_for('admin'))

@app.route('/agentcreation',methods=['POST'])
def agentcreation():
    agent = request.form['agent']
    email=request.form['email']
    password=request.form['password']
    sql = 'INSERT INTO AGENTS (AGENTID,EMAIL,PASSWORD) VALUES(?,?,?)'
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, agent)
    ibm_db.bind_param(stmt, 2, email)
    ibm_db.bind_param(stmt, 3, password)
    try:
        ibm_db.execute(stmt)
        return render_template('createagent.html',pred="Agent Created",admin=session['aname'])
    except:
        return render_template('createagent.html',pred="Agentid already exists ",admin=session['aname'])

@app.route('/agent')
def agent():
    if "agent" in session:
        return redirect(url_for('agenthome'))
    return render_template('agentlogin.html')

@app.route('/agentloginpage', methods=['POST'])
def agentloginpage():
    user = request.form['email']
    passw = request.form['password']
    sql = "SELECT * FROM AGENTS WHERE email =? AND password=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, user)
    ibm_db.bind_param(stmt, 2, passw)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    print(account)
    print(user, passw)
    if account:
        session['agent'] = user
        session['agentname'] = account['AGENTID']
        return redirect(url_for('agenthome'))
    else:
        flash("Login unsuccessful. Incorrect username / password !")
        return render_template('agentlogin.html')

@app.route('/agenthome')
def agenthome():
    if 'agent' in session:
        user=session['agent']
        username=session['agentname']
        sql1 = "SELECT COUNT(*) AS C1 FROM  COMPLAINTS WHERE C_STATUS=? AND AGENT=? "
        stmt = ibm_db.prepare(conn, sql1)
        ibm_db.bind_param(stmt, 1, "ADDRESSED")
        ibm_db.bind_param(stmt, 2, username)
        ibm_db.execute(stmt)
        addressed = ibm_db.fetch_assoc(stmt)
        print(addressed)
        sql2 = "SELECT COUNT(*) AS C2 FROM  COMPLAINTS WHERE C_STATUS=? AND AGENT=?"
        stmt = ibm_db.prepare(conn, sql2)
        ibm_db.bind_param(stmt, 1, "COMPLETED")
        ibm_db.bind_param(stmt, 2, username)
        ibm_db.execute(stmt)
        completed = ibm_db.fetch_assoc(stmt)
        print(completed)
        return render_template('agenthome.html',user=username,ac=addressed['C1'],c=completed['C2'])
    else:
        return redirect(url_for('agent'))


@app.route('/agviewcomplaints')
def agviewcomplaints():
    if 'agent' in session:
        return render_template('agviewcomplaints.html',user=session['agentname'])
    else:
        return redirect(url_for('agent'))

@app.route('/agentvcomplaint',methods=['POST'])
def agentvcomplaint():
    status=request.form["status"]
    sql = "SELECT DATE,COMPLAINT_ID,COMPLAINT,C_STATUS,U_EMAIL FROM COMPLAINTS WHERE C_STATUS=? AND AGENT=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, status)
    ibm_db.bind_param(stmt, 2, session['agentname'])
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    hist = []
    while account != False:
        hist.append(account)
        account = ibm_db.fetch_assoc(stmt)
    print(hist)
    if hist:
        df1 = pd.json_normalize(hist)
        print(df1)
        df1.index = df1.index + 1
        records1 = df1.to_records(index=False)
        hists=list(records1)

        print(account)
        return render_template('agviewcomplaints.html',user=session['agentname'],data=hists)
    else:
        return render_template('agviewcomplaints.html', pred="No complaints to view",user=session['agentname'])


@app.route('/closecomplaint')
def closecomplaint():
    if 'agent' in session:
        return render_template('closecomplaint.html',user=session['agentname'])
    else:
        return redirect(url_for('agent'))

@app.route('/close',methods=['POST'])
def close():
    c_id = request.form['cid']
    sql = "SELECT COMPLAINT,U_EMAIL,C_STATUS FROM COMPLAINTS WHERE COMPLAINT_ID=? AND AGENT=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, c_id)
    ibm_db.bind_param(stmt, 2, session['agentname'])
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    if account:
        if account['C_STATUS']=='COMPLETED':
            return render_template('closecomplaint.html', pred="customer issue already solved",user=session['agentname'])
        else:
            sql = "UPDATE COMPLAINTS SET C_STATUS=? WHERE COMPLAINT_ID =? AND C_STATUS=?"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt, 1, "COMPLETED")
            ibm_db.bind_param(stmt, 2, c_id)
            ibm_db.bind_param(stmt, 3, "ADDRESSED")
            ibm_db.execute(stmt)
            email = account['U_EMAIL']
            cid = c_id
            subject = "ISSUE SOLVED"
            body = f"Your complaint with ID-{cid} has been resolved."
            try:
                sendmail(subject=subject, receiver=email, body=body)
            except:
                pass
            return render_template('closecomplaint.html',pred="customer issue solved",admin=session['agentname'])
    else:
        return render_template('closecomplaint.html', pred="check complaint id ",admin=session['agentname'])


@app.route("/changepassword")
def changepassword():
    if 'agent' in session:
        return render_template('changepassword.html',user=session['agentname'])
    else:
        return redirect(url_for('agent'))

@app.route('/passw',methods=['POST'])
def password():
    newpass=request.form['newpass']
    sql="UPDATE AGENTS SET PASSWORD=? WHERE EMAIL=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1,newpass)
    ibm_db.bind_param(stmt, 2, session['agent'])
    ibm_db.execute(stmt)
    return render_template('changepassword.html',pred="password updated",user=session['agentname'])




@app.route("/logout")
def logout():
    if "user" in session:
        session.clear()
    return redirect(url_for("login"))

@app.route("/alogout")
def alogout():
    if "aemail" in session:
        session.clear()
    return redirect(url_for("admin"))

@app.route("/aglogout")
def aglogout():
    if "agent" in session:
        session.clear()
    return redirect(url_for("agent"))





if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080,debug=True)
