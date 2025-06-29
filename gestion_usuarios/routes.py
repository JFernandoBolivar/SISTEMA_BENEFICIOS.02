from flask import Blueprint, render_template, request, redirect, url_for, session,make_response,flash
import MySQLdb.cursors
from datetime import datetime
from extensions import mysql
from weasyprint import HTML
import bcrypt

gestion_usuarios_bp = Blueprint('gestion_usuarios', __name__)


# gestion de usuarios

@gestion_usuarios_bp.route("/usuarios", methods=["GET"])
def usuarios():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT usuarios.C_I AS Cedula, personal.Name_Com, usuarios.username, 
               personal.Location_Physical, personal.Location_Admin, usuarios.estado
        FROM usuarios
        JOIN personal ON usuarios.C_I = personal.Cedula
    ''')
    usuarios = cursor.fetchall()
    cursor.close()
    return render_template('usuarios.html', usuarios=usuarios)

# editar usuarios

@gestion_usuarios_bp.route("/editar_usuario/<int:cedula>", methods=["GET", "POST"])
def editar_usuario(cedula):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password'].strip()
     
        
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                UPDATE usuarios
                SET username = %s, Password = %s
                WHERE C_I = %s
            ''', (username, hashed_password, cedula))
        else:
            cursor.execute('''
                UPDATE usuarios
                SET username = %s
                WHERE C_I = %s
            ''', (username, cedula))
        
       
        mysql.connection.commit()
        cursor.close()
        flash("Usuario actualizado correctamente.", "success")
        return redirect(url_for('consultas.consult'))
    
    cursor.execute('''
        SELECT usuarios.C_I AS Cedula, personal.Name_Com, usuarios.username, 
               personal.Location_Physical, usuarios.Password, usuarios.estado
        FROM usuarios
        JOIN personal ON usuarios.C_I = personal.Cedula
        WHERE usuarios.C_I = %s
    ''', (cedula,))
    usuario = cursor.fetchone()
    cursor.close()
    
    return render_template('editar_usuario.html', usuario=usuario)

# suspender usuarios

@gestion_usuarios_bp.route("/suspender_usuario/<int:cedula>", methods=["POST"])
def suspender_usuario(cedula):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE usuarios SET estado = %s WHERE C_I = %s', ('suspendido', cedula))
    mysql.connection.commit()
    
    cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                  (session['cedula'], session['username'], f'Suspendio el usuario {cedula}', datetime.now()))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('gestion_usuarios.usuarios'))


# reactivar usuarios

@gestion_usuarios_bp.route("/reactivar_usuario/<int:cedula>", methods=["POST"])
def reactivar_usuario(cedula):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE usuarios SET estado = %s WHERE C_I = %s', ('activo', cedula))
    mysql.connection.commit()
    cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                  (session['cedula'], session['username'], f'Reactivo el usuario {cedula}', datetime.now()))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('gestion_usuarios.usuarios'))


# reporte de usuarios

@gestion_usuarios_bp.route("/reporte_usuarios", methods=["GET","POST"])
def reporte_usuarios():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user_history')
    historial = cursor.fetchall()
    mysql.connection.commit()
    cursor.close()
    return render_template('reporte_usuarios.html', historial=historial)


# reportes del personal
@gestion_usuarios_bp.route("/reporte_personal", methods=["GET","POST"])
def reporte_personal():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT * FROM user_history
        WHERE cedula_personal IS NOT NULL AND cedula_personal != ''
          AND Name_personal IS NOT NULL AND Name_personal != ''
    ''')
    historial = cursor.fetchall()
    cursor.close()
    return render_template('reporte_personal.html', historial=historial)



@gestion_usuarios_bp.route("/reporte_personalPDF", methods=["GET", "POST"])
def reporte_personalPDF():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))

    nombre = request.args.get('nombre', '').strip()
    fecha = request.args.get('fecha', '').strip()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = '''
        SELECT * FROM user_history
        WHERE cedula_personal IS NOT NULL AND cedula_personal != ''
          AND Name_personal IS NOT NULL AND Name_personal != ''
    '''
    params = []

    if nombre:
        query += " AND Name_personal LIKE %s"
        params.append(f"%{nombre}%")
    if fecha:
        query += " AND DATE(time_login) = %s"
        params.append(fecha)

    cursor.execute(query, params)
    historial = cursor.fetchall()
    cursor.close()

    if request.args.get('pdf') == '1':
        rendered = render_template('reporte_personal_pdf.html', historial=historial, nombre=nombre, fecha=fecha)
        pdf = HTML(string=rendered).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=reporte_personal.pdf'
        return response

    return render_template('reporte_personalPDF.html', historial=historial, nombre=nombre, fecha=fecha)

@gestion_usuarios_bp.route("/nuevoEmpActivo", methods=["GET", "POST"])
def NuevoUserActivo():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    if request.method == "POST":
        cedula = request.form['cedula']
        nombreCompleto = request.form['nombreCompleto']
        unidadFisica = request.form['unidadFisica']
        unidadAdmin = request.form['unidadAdmin']
        observacion = request.form['observacion']
        CIFamiliar = request.form.get('cedula-family', None)
        Nombre_Familiar = request.form.get('Nombre_Familiar', None)
        CodigoCarnet = request.form.get('CodigoCarnet', None)
        estatus = 1
        cedula_personal = session['cedula']
        lunch = 1 if 'lunch' in request.form else 0
        horaEntrega = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM personal WHERE Cedula = %s', (cedula,))
            existing_user = cursor.fetchone()

            if existing_user:
                cursor.close()
                return render_template("nuevo_user_activo.html", error="Esta cédula ya está registrada.")

            cursor.execute('''
                INSERT INTO personal (Cedula, Name_Com, Code, Location_Physical, Location_Admin, manually, Estatus) 
                VALUES (%s, %s, %s, %s, %s, 1, %s)
            ''', (cedula, nombreCompleto, CodigoCarnet, unidadFisica, unidadAdmin, estatus))
            mysql.connection.commit()
            
            cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                           (session['cedula'], session['username'], f'Registró un personal activo con cédula {cedula}', datetime.now()))
            mysql.connection.commit()

            if CIFamiliar and Nombre_Familiar:
                cursor.execute('''
                    INSERT INTO autorizados (beneficiado, Nombre, Cedula)
                    VALUES (%s, %s, %s)
                ''', (cedula, Nombre_Familiar, CIFamiliar))
                mysql.connection.commit()

            cursor.execute('''
                INSERT INTO delivery (Time_box, Data_ID, Staff_ID, Observation, Lunch) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (horaEntrega, cedula, cedula_personal, observacion, lunch))
            mysql.connection.commit()
    
            cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                          (session['cedula'], session['username'], f'Registró entrega para {cedula}', datetime.now()))
            mysql.connection.commit()
            
            cursor.close()
            return render_template("nuevo_user_activo.html", success="Registro exitoso.")  
        except Exception as e:
            return render_template("nuevo_user_activo.html", error=f"Error en el registro: {str(e)}")
    return render_template("nuevo_user_activo.html")

@gestion_usuarios_bp.route("/nuevoEmpPasivo", methods=["GET", "POST"])
def NuevoUserPasivo():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    if request.method == "POST":
        cedula = request.form['cedula']
        nombreCompleto = request.form['nombreCompleto']
        observacion = request.form['observacion']
        CIFamiliar = request.form.get('cedula-family', None)
        Nombre_Familiar = request.form.get('Nombre_Familiar', None)
        CodigoCarnet = request.form.get('CodigoCarnet', None)
        estatus = 2
        estado = request.form['estado']
        cedula_personal = session['cedula']
        lunch = 1 if 'lunch' in request.form else 0
        horaEntrega = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM personal WHERE Cedula = %s', (cedula,))
            existing_user = cursor.fetchone()

            if existing_user:
                cursor.close()
                return render_template("nuevo_user_pasivo.html", error="Esta cédula ya está registrada.")

            cursor.execute('''
                INSERT INTO personal (Cedula, Name_Com, Code, manually, Estatus, ESTADOS) 
                VALUES (%s, %s, %s, 1, %s, %s)
            ''', (cedula, nombreCompleto, CodigoCarnet, estatus, estado))
            mysql.connection.commit()


            cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                           (session['cedula'], session['username'], f'Registró un personal pasivo con cédula {cedula}', datetime.now()))
            mysql.connection.commit()

            if CIFamiliar and Nombre_Familiar:
                cursor.execute('''
                    INSERT INTO autorizados (beneficiado, Nombre, Cedula)
                    VALUES (%s, %s, %s)
                ''', (cedula, Nombre_Familiar, CIFamiliar))
                mysql.connection.commit()

            cursor.execute('''
                INSERT INTO delivery (Time_box, Data_ID, Staff_ID, Observation, Lunch) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (horaEntrega, cedula, cedula_personal, observacion, lunch))
            mysql.connection.commit()
            
            cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                          (session['cedula'], session['username'], f'Registró entrega para {cedula}', datetime.now()))
            mysql.connection.commit()
            
            cursor.close()
            return render_template("nuevo_user_pasivo.html", success="Registro exitoso.")  
        except Exception as e:
            return render_template("nuevo_user_pasivo.html", error=f"Error en el registro: {str(e)}")
    return render_template("nuevo_user_pasivo.html")