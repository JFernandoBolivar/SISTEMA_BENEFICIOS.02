from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify,flash
import MySQLdb.cursors
from datetime import datetime, timedelta
from extensions import mysql

consultas_bp = Blueprint('consultas', __name__)

def get_stats(cursor, fecha=None, tipo_usuario='general'):
    """datos de entregas según filtros"""
    queries = {
        'activos': {
            'personas': 'SELECT COUNT(*) AS total_personas FROM personal WHERE Estatus = 1',
            'recibido': '''SELECT COUNT(*) AS total_recibido 
                          FROM delivery d 
                          JOIN personal p ON d.Data_ID = p.Cedula 
                          WHERE p.Estatus = 1'''
        },
        'pasivos': {
            'personas': 'SELECT COUNT(*) AS total_personas FROM personal WHERE Estatus = 2',
            'recibido': '''SELECT COUNT(*) AS total_recibido 
                          FROM delivery d 
                          JOIN personal p ON d.Data_ID = p.Cedula 
                          WHERE p.Estatus = 2'''
        },
        'comision_servicios_alert': {
            'personas': 'SELECT COUNT(*) AS total_personas FROM personal WHERE Estatus IN (9, 11)',
            'recibido': '''SELECT COUNT(*) AS total_recibido 
                          FROM delivery d 
                          JOIN personal p ON d.Data_ID = p.Cedula 
                          WHERE p.Estatus IN (9, 11)'''
        },
        'comision_servicios_2': {
            'personas': 'SELECT COUNT(*) AS total_personas FROM personal WHERE Estatus = 10',
            'recibido': '''SELECT COUNT(*) AS total_recibido 
                          FROM delivery d 
                          JOIN personal p ON d.Data_ID = p.Cedula 
                          WHERE p.Estatus = 10'''
        },
        'general': {
            'personas': 'SELECT COUNT(*) AS total_personas FROM personal',
            'recibido':  
       'SELECT COUNT(*) AS total_recibido FROM delivery d WHERE d.Time_box >= DATE_SUB(CURDATE(), INTERVAL 15 DAY)'
    
        }
    }
    
    query = queries.get(tipo_usuario, queries['general'])
    
    # Ejecutar consulta para total de personas
    cursor.execute(query['personas'])
    total_personas = cursor.fetchone()['total_personas']
    
    # Ejecutar consulta para entregas recibidas con filtro de fecha
    recibido_query = query['recibido']
    if fecha:
        if 'WHERE' in recibido_query:
            recibido_query += f' AND DATE(d.Time_box) = "{fecha}"'
        else:
            recibido_query = recibido_query.replace(';', '') + f' WHERE DATE(Time_box) = "{fecha}"'
    
    cursor.execute(recibido_query)
    total_recibido = cursor.fetchone()['total_recibido']
    
    return {
        'total_personas': total_personas,
        'total_recibido': total_recibido,
        'faltan': total_personas - total_recibido
    }

@consultas_bp.route("/", methods=["GET", "POST"])
def consult():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    super_admin = session.get('Super_Admin', 0)
    fecha = request.form.get('fecha')
    tipo_usuario = request.form.get('tipo_usuario', 'general')
    cedula = request.form.get('cedula')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Forzar fecha actual para no super_admins
    if super_admin == 0:
        fecha = datetime.now().strftime('%Y-%m-%d')
    
    # Búsqueda por cédula
    if cedula:
        cursor.execute('''
            SELECT 
                p.Cedula, 
                p.Name_Com, 
                p.Location_Physical, 
                p.Location_Admin, 
                p.Estatus,
                p.ESTADOS,
                EXISTS(
                    SELECT 1 
                    FROM delivery d 
                    WHERE d.Data_ID = p.Cedula 
                    AND d.Time_box >= CURDATE() - INTERVAL 15 DAY
                ) AS Entregado_recientemente
            FROM personal p
            WHERE p.Cedula = %s
        ''', (cedula,))
        data_exit = cursor.fetchone()

        if not data_exit:
            stats = get_stats(cursor)
            cursor.close()
            return render_template('index.html', 
                super_admin=super_admin,
                mensaje="Cédula no encontrada",
                cedula=cedula,
                **stats
            )

        estatus = data_exit['Estatus']
        # Manejo de diferentes estatus
        if estatus in [3, 4, 5, 6]:
            mensajes = {
                3: "Suspendido por trámites administrativos.",
                4: "Suspendido por verificar.",
                5: "No puede retirar. Está fuera del país.",
                6: "Personal Fallecido"
            }
            cursor.close()
            return render_template('index.html', 
                super_admin=super_admin,
                mensaje=mensajes[estatus],
                cedula=cedula
            )
        
        elif estatus == 9:
            cursor.close()
            return render_template('index.html', 
                super_admin=super_admin, 
                mensaje="Comisión vencida",
                mensaje2='Comunicarse con el Supervisor o administrador',
                cedula=cedula, 
                mostrar_boton=True
            )
        
        elif estatus in [1, 2, 10, 11]:
            tipo = 'activos' if estatus == 1 else 'pasivos'
            stats = get_stats(cursor, tipo_usuario=tipo)
            cursor.close()
            return render_template('index.html', 
                super_admin=super_admin, 
                data=data_exit, 
                **stats
            )
        
        else:
            cursor.close()
            return render_template('index.html', 
                super_admin=super_admin, 
                mensaje="Estatus no permitido para retirar",
                mensaje2='Comunicarse con el administrador',
                cedula=cedula
            )

    # Búsqueda general (sin cédula)
    stats = get_stats(cursor, fecha, tipo_usuario)
    cursor.close()
    
    return render_template('index.html', 
        super_admin=super_admin, 
        fecha=fecha,
        tipo_usuario=tipo_usuario,
        **stats
    )

@consultas_bp.route("/registrar", methods=["POST"])
def registrar():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cedula = request.form['cedula']
    cedula_personal = request.form['cedula_personal']
    super_admin = session.get('Super_Admin', 0)
    CIFamily = request.form.get('cedulafamiliar')
    lunch = 1 if request.form.get('lunch') == '1' else 0 
    
    # Forzar fecha actual para no super_admins
    fecha = datetime.now().strftime('%Y-%m-%d') if super_admin == 0 else request.form.get('fecha')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        # Validar autorizado único en todo el sistema
        if CIFamily:
            cursor.execute('SELECT COUNT(*) AS total FROM autorizados WHERE Cedula = %s', (CIFamily,))
            if cursor.fetchone()['total'] > 0:
                raise Exception("La cédula del autorizado ya está registrada en el sistema")

        # Buscar titular
        cursor.execute('SELECT * FROM personal WHERE Cedula = %s', (cedula,))
        titular = cursor.fetchone()
        
        if not titular:
            raise Exception("La cédula no se encuentra en la tabla personal")

        # Verificar entregas recientes
        cursor.execute('''
            SELECT COUNT(*) AS entregas_recientes
            FROM delivery 
            WHERE Data_ID = %s 
            AND Time_box >= CURDATE() - INTERVAL 15 DAY
        ''', (titular['Cedula'],))
        if cursor.fetchone()['entregas_recientes'] > 0:
            raise Exception("Ya existe una entrega registrada en los últimos 15 días")

        # Registrar entrega
        observacion = request.form.get('observacion', '').upper()
        nameFamily = request.form.get('nombrefamiliar', '').upper()
        hora_entrega = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO delivery (Time_box, Staff_ID, Observation, Data_ID, Lunch) 
            VALUES (%s, %s, %s, %s, %s)
        ''', (hora_entrega, cedula_personal, observacion, titular['Cedula'], lunch))

        # Registrar autorizado si corresponde
        if titular['Estatus'] == 2 and CIFamily and nameFamily:
            cursor.execute('''
                INSERT INTO autorizados (beneficiado, Nombre, Cedula)
                VALUES (%s, %s, %s)
            ''', (titular['Cedula'], nameFamily, CIFamily))

        # Registrar en historial 
        cursor.execute('''
            INSERT INTO user_history (
                cedula, 
                Name_user, 
                action, 
                time_login,
                cedula_personal,
                Name_personal,
                Cedula_autorizado,
                Name_autorizado
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            session['cedula'],
            session['username'],
            f'Marco como entregado el beneficio a {titular['Cedula']}',
            datetime.now(),
            titular['Cedula'],
            titular['Name_Com'],
            CIFamily if CIFamily else None,
            nameFamily if nameFamily else None
        ))
        
        mysql.connection.commit()
        stats = get_stats(cursor, fecha)
        return render_template('index.html', 
            mensaje="Registro exitoso.",
            mensaje2="El registro se ha completado correctamente.",
            cedula=cedula,
            **stats
        )

    except Exception as e:
        mysql.connection.rollback()
        stats = get_stats(cursor, fecha)
        return render_template('index.html', 
            mensaje="Error en registro",
            mensaje2=str(e),
            cedula=cedula,
            **stats
        )
        
    finally:
        cursor.close()


@consultas_bp.route("/registrar_apoyo", methods=["GET", "POST"])
def registrar_apoyo():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))

    mensaje = None

    if request.method == "POST":
        ci_autorizado = request.form['ci_autorizado']
        nombre_autorizado = request.form['nombre_autorizado']
        cantidad = request.form['cantidad']

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO apoyo (CI_autorizado, Nombre_autorizado, cantidad,Fecha) VALUES (%s, %s, %s,%s)",
            (ci_autorizado, nombre_autorizado, cantidad,datetime.now())
        )
         # Registrar en historial con nuevos campos
        cursor.execute('''
            INSERT INTO user_history (
                cedula, 
                Name_user, 
                action, 
                time_login,
                Cedula_autorizado,
                Name_autorizado
            ) 
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            session['cedula'],
            session['username'],
            f'Registró entrega de apoyo a {ci_autorizado}',
            datetime.now(),
            ci_autorizado,
            nombre_autorizado
        ))
        mysql.connection.commit()
        cursor.close()
        flash("Registro guardado correctamente.", "success") 
        return redirect(url_for('consultas.consult'))

    return render_template("index.html", mensaje=mensaje)
    

# EDITAR EL ESTATUS DE LOS USUARIOS
@consultas_bp.route("/cambiar_estatus", methods=["GET", "POST"])
def cambiar_estatus():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == "POST":
        cedula = request.form['cedula']
        nuevo_estatus = request.form['estatus']
        
        
        cursor.execute('SELECT Estatus FROM personal WHERE Cedula = %s', (cedula,))
        estatus_actual = cursor.fetchone()['Estatus']
        
       
        estatus_nombres = {
              1: "Activo",
              2: "Pasivo",
              3: "Suspendidos por trámites administrativos",
              5: "Fuera del país",
              6: "Fallecidos",
              7: "Se requiere confirmación",
              9: "Comisión de Servicio (Vencida)",
             10: "Comisión de Servicio (vigente)"
        }
        
        estatus_actual_nombre = estatus_nombres.get(estatus_actual, "Desconocido")
        nuevo_estatus_nombre = estatus_nombres.get(int(nuevo_estatus), "Desconocido")
        
       
        cursor.execute('UPDATE personal SET Estatus = %s WHERE Cedula = %s', (nuevo_estatus, cedula))
        mysql.connection.commit()
        

        cursor.execute(
    'INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)',
    (session['cedula'], session['username'], f'Cambió el estatus de la cédula {cedula} de {estatus_actual_nombre} a {nuevo_estatus_nombre}', datetime.now())
)
        mysql.connection.commit()
        
        cursor.close()
        return redirect(url_for('consultas.cambiar_estatus'))
    
    cursor.execute('SELECT Cedula, Code, Name_Com, Estatus FROM personal ')
    usuarios = cursor.fetchall()
    cursor.execute('SELECT COUNT(*) AS total_personas FROM personal')
    total_personas = cursor.fetchone()['total_personas']
    cursor.close()
    return render_template('cambiar_estatus.html', usuarios=usuarios, total_personas=total_personas)

@consultas_bp.route("/obtener_autorizados", methods=["GET"])
def obtener_autorizados():
    if 'loggedin' not in session:
        return jsonify({"error": "No autorizado"}), 403

    cedula_titular = request.args.get('cedula')
    if not cedula_titular:
        return jsonify({"error": "Cédula del titular no proporcionada"}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        # Obtener estatus del titular
        cursor.execute('''
            SELECT Estatus 
            FROM personal 
            WHERE Cedula = %s
        ''', (cedula_titular,))
        titular = cursor.fetchone()
        
        if not titular:
            return jsonify({"error": "Titular no encontrado"}), 404
        
        # Obtener autorizados usando Cedula como referencia
        cursor.execute('''
            SELECT Cedula, Nombre
            FROM autorizados
            WHERE beneficiado = %s
        ''', (cedula_titular,))
        autorizados = cursor.fetchall()
        
        if not autorizados:
            return jsonify({"info": "Sin autorizados registrados"})
        
        # Construir respuesta
        return jsonify([{
            "Cedula_autorizado": a['Cedula'],
            "Nombre_autorizado": a['Nombre'],
            "estatus": titular['Estatus']
        } for a in autorizados])
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener autorizados: {str(e)}"}), 500
    finally:
        cursor.close()