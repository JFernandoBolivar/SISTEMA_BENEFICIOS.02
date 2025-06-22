# auth/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session
import MySQLdb.cursors
import bcrypt
from datetime import datetime
from datetime import timedelta
from extensions import mysql

auth_bp = Blueprint('auth', __name__)

# inicios de sesion
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        cedula = request.form['cedula']
        password = request.form['password']
        
        if not cedula or not password:
            error = "Cédula y contraseña son requeridas"
            return render_template('login.html', error=error)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM usuarios WHERE C_I = %s', (cedula,))
        user = cursor.fetchone()

        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user['Password'].encode('utf-8')):
                if user['estado'] == 'suspendido':
                    error = "Tu cuenta está suspendida. Contacta al administrador."
                    return render_template('login.html', error=error)

                session['loggedin'] = True
                session['cedula'] = user['C_I']  # Actualizado a C_I
                session['username'] = user['username']
                session['Super_Admin'] = user['Super_Admin']
                # CAMBIO: Guardar como string ISO en lugar de datetime
                session['time_login'] = datetime.now().isoformat()
                
                # Adaptado a nueva estructura de user_history
                cursor.execute(
                    'INSERT INTO user_history (cedula, Name_user, action, time_login) '
                    'VALUES (%s, %s, %s, %s)',
                    (session['cedula'], session['username'], 'sesion iniciada', datetime.now())
                )
                mysql.connection.commit()
                cursor.close()
                return redirect(url_for('consultas.consult'))
            else:
                error = "Cédula o contraseña incorrecta"
                return render_template('login.html', error=error)
        else:
            error = "Cédula o contraseña incorrecta"
            return render_template('login.html', error=error)

    return render_template('login.html')



@auth_bp.route("/logout")
def logout():
    cedula = session.get('cedula')
    username = session.get('username')
    time_login_str = session.get('time_login')

    time_login = None
    if time_login_str:
        try:
            time_login = datetime.fromisoformat(time_login_str)
            if time_login.tzinfo is not None:
                time_login = time_login.replace(tzinfo=None)
        except Exception:
            time_login = None

    time_finish = datetime.now()
    if time_finish.tzinfo is not None:
        time_finish = time_finish.replace(tzinfo=None)

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'INSERT INTO user_history (cedula, Name_user, action, time_login, time_finish) '
        'VALUES (%s, %s, %s, %s, %s)',
        (cedula, username, 'sesion cerrada', time_login, time_finish)
    )
    mysql.connection.commit()
    cursor.close()

    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route("/RegistUser", methods=["GET", "POST"])
def RegistUser():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == "POST":
        cedula = request.form['cedula']
        username = request.form['username'].strip().upper()
        password = request.form['password'].replace(" ", "") 
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute('SELECT * FROM personal WHERE Cedula = %s', (cedula,))
        data_user = cursor.fetchone()
        
        if not data_user or data_user['Estatus'] !=1:
            cursor.close()
            return render_template("regisLogin.html", error="Usted no forma parte del personal activo")
        
        # Cambiado a C_I
        cursor.execute('SELECT * FROM usuarios WHERE C_I = %s', (cedula,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            return render_template("regisLogin.html", error="La cédula ya está registrada en el sistema")
        
        cursor.execute('SELECT * FROM usuarios WHERE username = %s', (username,))
        existing_username = cursor.fetchone()
        
        if existing_username:
            cursor.close()
            return render_template("regisLogin.html", error="El nombre de usuario no está disponible")
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Cambiado a C_I
        cursor.execute('INSERT INTO usuarios (C_I, username, Password) VALUES (%s, %s, %s)', 
                       (cedula, username, hashed_password))
        mysql.connection.commit()
  
        # Adaptado a user_history
        cursor.execute(
            'INSERT INTO user_history (cedula, Name_user, action, time_login) '
            'VALUES (%s, %s, %s, %s)', 
            (cedula, username, f'Registro al usuario {cedula}', datetime.now())
        )
        mysql.connection.commit()
        cursor.close()
        
        return render_template("regisLogin.html", success="Registro exitoso.")
    
    return render_template("regisLogin.html")

@auth_bp.route("/tipo_user", methods=["GET", "POST"])
def tipo_user():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":
        cedula = request.form['cedula']
        nuevo_estatus = request.form['super_admin']

        try:
            cursor.execute('SELECT COUNT(*) AS total_personas FROM usuarios')
            total_personas = cursor.fetchone()['total_personas']
            # Cambiado a C_I
            cursor.execute(
                'UPDATE usuarios SET Super_Admin = %s WHERE C_I = %s',
                (nuevo_estatus, cedula)
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return render_template("cambiar_super_admin.html", total_personas=total_personas, error=f"Error al actualizar: {str(e)}")

  
    cursor.execute('SELECT C_I AS Cedula, username, Super_Admin FROM usuarios')
    usuarios = cursor.fetchall()
    cursor.execute('SELECT COUNT(*) AS total_personas FROM usuarios')
    total_personas = cursor.fetchone()['total_personas']
    cursor.close()

    return render_template("cambiar_super_admin.html", usuarios=usuarios, total_personas=total_personas)