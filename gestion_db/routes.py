from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, flash, get_flashed_messages
import MySQLdb.cursors
import pandas as pd
from datetime import datetime
import os
import subprocess
from functools import wraps
from extensions import mysql
from config import Config
from openpyxl import Workbook

gestion_db_bp = Blueprint('gestion_db', __name__)

#  verificar permisos de super admin
def requiere_super_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth.login'))
        if session.get('Super_Admin') != 1:
            flash("No tiene permisos para realizar esta acción", "danger")
            return redirect(url_for('gestion_db.gestionar_data'))
        return func(*args, **kwargs)
    return wrapper

#  validar estructura del Excel
def validar_estructura_excel(df):
    columnas_requeridas = [
        "Cedula", "Name_Com", "Code", 
        "Location_Physical", "Location_Admin", 
        "Estatus", "ESTADOS"
    ]
    faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas requeridas faltantes: {', '.join(faltantes)}")
    
    # Verificar que cédulas sean únicas
    if df['Cedula'].duplicated().any():
        duplicados = df[df['Cedula'].duplicated()]['Cedula'].unique()
        raise ValueError(f"Cédulas duplicadas encontradas: {', '.join(map(str, duplicados))}")

# procesar y limpiar datos
def procesar_datos(df):
    numericas = ["Cedula", "Code", "Estatus"]
    for col in numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    # Convertir columnas de texto
    texto = ["Name_Com", "Location_Physical", "Location_Admin", "ESTADOS"]
    for col in texto:
        df[col] = df[col].astype(str).str.strip().replace('nan', '')
    
    # Columna opcional
    if "manually" not in df.columns:
        df["manually"] = 0
    else:
        df["manually"] = df["manually"].fillna(0).astype(int)
    
    return df

# Función principal para cargar datos
def cargar_excel_a_db(file):
    try:
        # Leer y validar archivo
        df = pd.read_excel(file)
        validar_estructura_excel(df)
        df = procesar_datos(df)
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        stats = {
            'personal': {'insertados': 0, 'actualizados': 0},
            'autorizados': {'insertados': 0, 'actualizados': 0}
        }
        
        # Procesar cada registro
        for _, row in df.iterrows():
            # Buscar o crear registro de personal
            cursor.execute('SELECT ID FROM personal WHERE Cedula = %s', (row['Cedula'],))
            personal = cursor.fetchone()
            
            if personal:
                # Actualizar registro existente
                cursor.execute('''
                    UPDATE personal SET 
                        Name_Com = %s, Code = %s, Location_Physical = %s, 
                        Location_Admin = %s, manually = %s, Estatus = %s, ESTADOS = %s
                    WHERE ID = %s
                ''', (
                    row['Name_Com'], row['Code'], row['Location_Physical'],
                    row['Location_Admin'], row['manually'], row['Estatus'],
                    row['ESTADOS'], personal['ID']
                ))
                stats['personal']['actualizados'] += 1
                personal_id = personal['ID']
            else:
                # Insertar nuevo registro
                cursor.execute('''
                    INSERT INTO personal 
                    (Cedula, Name_Com, Code, Location_Physical, Location_Admin, 
                     manually, Estatus, ESTADOS)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    row['Cedula'], row['Name_Com'], row['Code'],
                    row['Location_Physical'], row['Location_Admin'], 
                    row['manually'], row['Estatus'], row['ESTADOS']
                ))
                stats['personal']['insertados'] += 1
                personal_id = cursor.lastrowid
            
            # Procesar autorizados si existen en el Excel
            if all(col in df.columns for col in ['Cedula_autorizado', 'Nombre_autorizado']):
                cedula_aut = str(row['Cedula_autorizado']).strip()
                nombre_aut = str(row['Nombre_autorizado']).strip()
                
                if cedula_aut and cedula_aut != 'nan' and nombre_aut and nombre_aut != 'nan':
                    cursor.execute('''
                        SELECT ID FROM autorizados 
                        WHERE Cedula = %s AND beneficiado = %s
                    ''', (cedula_aut, personal_id))
                    aut_existente = cursor.fetchone()
                    
                    if aut_existente:
                        cursor.execute('''
                            UPDATE autorizados SET Nombre = %s WHERE ID = %s
                        ''', (nombre_aut, aut_existente['ID']))
                        stats['autorizados']['actualizados'] += 1
                    else:
                        cursor.execute('''
                            INSERT INTO autorizados (beneficiado, Nombre, Cedula)
                            VALUES (%s, %s, %s)
                        ''', (personal_id, nombre_aut, cedula_aut))
                        stats['autorizados']['insertados'] += 1
        
        mysql.connection.commit()
        return stats
        
    except Exception as e:
        mysql.connection.rollback()
        raise e
    finally:
        cursor.close()

# Ruta para cargar datos desde Excel

@gestion_db_bp.route("/cargar_data", methods=["POST", "GET"])
@requiere_super_admin
def cargar_data():
    cursor = None
    try:
        if 'file' not in request.files or request.files['file'].filename == '':
            flash("Debe seleccionar un archivo Excel válido", "danger")
            return redirect(url_for('gestion_db.gestionar_data'))
        
        file = request.files['file']
        if not file.filename.lower().endswith('.xlsx'):
            flash("El archivo debe tener extensión .xlsx", "danger")
            return redirect(url_for('gestion_db.gestionar_data'))
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        df = pd.read_excel(file)
        validar_estructura_excel(df)
        df = procesar_datos(df)
        
        stats = {
            'personal': {'insertados': 0, 'actualizados': 0},
            'autorizados': {'insertados': 0, 'actualizados': 0}
        }
        
        for _, row in df.iterrows():
            # Buscar registro de personal por Cédula
            cursor.execute('SELECT Cedula FROM personal WHERE Cedula = %s', (row['Cedula'],))
            personal = cursor.fetchone()
            
            if personal:
                # Actualizar registro existente
                cursor.execute('''
                    UPDATE personal SET 
                        Name_Com = %s, Code = %s, Location_Physical = %s, 
                        Location_Admin = %s, manually = %s, Estatus = %s, ESTADOS = %s
                    WHERE Cedula = %s
                ''', (
                    row['Name_Com'], row['Code'], row['Location_Physical'],
                    row['Location_Admin'], row['manually'], row['Estatus'],
                    row['ESTADOS'], row['Cedula']
                ))
                stats['personal']['actualizados'] += 1
                beneficiado_cedula = row['Cedula']
            else:
                # Insertar nuevo registro
                cursor.execute('''
                    INSERT INTO personal 
                    (Cedula, Name_Com, Code, Location_Physical, Location_Admin, 
                     manually, Estatus, ESTADOS)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    row['Cedula'], row['Name_Com'], row['Code'],
                    row['Location_Physical'], row['Location_Admin'], 
                    row['manually'], row['Estatus'], row['ESTADOS']
                ))
                stats['personal']['insertados'] += 1
                beneficiado_cedula = row['Cedula']
            
            # Procesar autorizados usando Cédula como referencia
            if all(col in df.columns for col in ['Cedula_autorizado', 'Nombre_autorizado']):
                cedula_aut = str(row['Cedula_autorizado']).strip()
                nombre_aut = str(row['Nombre_autorizado']).strip()
                
                if cedula_aut and cedula_aut != 'nan' and nombre_aut and nombre_aut != 'nan':
                    cursor.execute('''
                        SELECT ID FROM autorizados 
                        WHERE Cedula = %s AND beneficiado = %s
                    ''', (cedula_aut, beneficiado_cedula))
                    aut_existente = cursor.fetchone()
                    
                    if aut_existente:
                        cursor.execute('''
                            UPDATE autorizados SET Nombre = %s WHERE ID = %s
                        ''', (nombre_aut, aut_existente['ID']))
                        stats['autorizados']['actualizados'] += 1
                    else:
                        cursor.execute('''
                            INSERT INTO autorizados (beneficiado, Nombre, Cedula)
                            VALUES (%s, %s, %s)
                        ''', (beneficiado_cedula, nombre_aut, cedula_aut))
                        stats['autorizados']['insertados'] += 1
        
        mysql.connection.commit()
        flash(
            f"Datos cargados exitosamente: "
            f"{stats['personal']['insertados']} nuevos registros, "
            f"{stats['personal']['actualizados']} actualizados | "
            f"{stats['autorizados']['insertados']} autorizados nuevos, "
            f"{stats['autorizados']['actualizados']} actualizados",
            "success"
        )
    
    except pd.errors.EmptyDataError:
        flash("El archivo Excel está vacío", "danger")
    except ValueError as e:
        flash(f"Error en los datos: {str(e)}", "danger")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al procesar el archivo: {str(e)}", "danger")
    finally:
        if cursor is not None:
            cursor.close()
    
    return redirect(url_for('gestion_db.gestionar_data'))

# Ruta para vaciar la base de datos
@gestion_db_bp.route("/vaciar_db", methods=["POST"])
@requiere_super_admin
def vaciar_db():
   
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener conteo antes de vaciar (solo tabla personal)
        cursor.execute("SELECT COUNT(*) AS total FROM personal")
        result = cursor.fetchone()
        total_personal = result['total'] if result else 0
        
        # Vaciar solo la tabla personal manteniendo integridad referencial
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE personal")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Registrar acción en el historial
        cursor.execute('''
            INSERT INTO user_history (cedula, Name_user, action, time_login) 
            VALUES (%s, %s, %s, %s)
        ''', (
            session['cedula'], 
            session['username'], 
            f'Vació tabla personal: {total_personal} registros eliminados',
            datetime.now()
        ))
        mysql.connection.commit()
        
        flash(
            f"Tabla personal vaciada correctamente: {total_personal} registros eliminados",
            "success"
        )
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al vaciar la tabla personal: {str(e)}", "danger")
    finally:
        cursor.close()
    
    return redirect(url_for('gestion_db.gestionar_data'))

# Función para generar backup en Excel
def generar_backup_excel():
    cursor = None
    try:
        # Configuración inicial
        backup_dir = os.path.join(Config.BACKUP_FOLDER)
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data_benficios_{timestamp}.xlsx'
        filepath = os.path.join(backup_dir, filename)
        
        # Conexión a la base de datos
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        tablas = ['personal', 'autorizados', 'delivery', 'user_history']
        tablas_exportadas = 0

        # Usar with para asegurar el cierre del writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            wb = writer.book
            # Crear hoja temporal inicial (requerido por openpyxl)
            wb.create_sheet("Temporal")
            
            for tabla in tablas:
                try:
                    # Verificar si la tabla existe
                    cursor.execute(f"SHOW TABLES LIKE '{tabla}'")
                    if not cursor.fetchone():
                        continue
                    
                    # Obtener estructura de la tabla
                    cursor.execute(f"DESCRIBE {tabla}")
                    columnas = [col[0] for col in cursor.fetchall()]
                    
                    # Obtener datos con paginación para tablas grandes
                    cursor.execute(f"SELECT COUNT(*) as total FROM {tabla}")
                    total_registros = cursor.fetchone()['total']
                    
                    print(f"Tabla: {tabla}, Total registros: {total_registros}")  # Debug
                    
                    if total_registros == 0:
                        df = pd.DataFrame(columns=columnas)
                    elif total_registros > 10000:
                        # Procesamiento por chunks para tablas grandes
                        chunk_size = 5000
                        df_list = []
                        for offset in range(0, total_registros, chunk_size):
                            cursor.execute(f"SELECT * FROM {tabla} LIMIT {chunk_size} OFFSET {offset}")
                            chunk = cursor.fetchall()
                            df_list.append(pd.DataFrame(chunk))
                        df = pd.concat(df_list, ignore_index=True)
                    else:
                        cursor.execute(f"SELECT * FROM {tabla}")
                        data = cursor.fetchall()
                        df = pd.DataFrame(data)
                    
                    # Asegurar estructura de columnas
                    df = df.reindex(columns=columnas, fill_value=None)
                    
                    # Escribir hoja en el Excel
                    df.to_excel(writer, sheet_name=tabla[:31], index=False)
                    tablas_exportadas += 1
                    
                except Exception as e:
                    flash(f"Error al exportar tabla {tabla}: {str(e)}", "warning")
                    continue
            
            # Eliminar hoja temporal si se exportaron tablas
            if tablas_exportadas > 0 and "Temporal" in wb.sheetnames:
                wb.remove(wb["Temporal"])
            
            # Si no se exportó ninguna tabla, crear una hoja con mensaje
            if tablas_exportadas == 0:
                df = pd.DataFrame({"Mensaje": ["No se encontraron datos para exportar"]})
                df.to_excel(writer, sheet_name="Información", index=False)
        
        # Registrar acción en el historial
        cursor.execute('''
            INSERT INTO user_history (cedula, Name_user, action, time_login) 
            VALUES (%s, %s, %s, %s)
        ''', (
            session['cedula'], session['username'], 
            'Generó backup Excel de la base de datos', 
            datetime.now()
        ))
        mysql.connection.commit()
        
        # Eliminar el archivo después de enviarlo 
        def cleanup():
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
        
        response = send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response.call_on_close(cleanup)
        
        return response
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al generar copia de seguridad en Excel: {str(e)}", "danger")
        return redirect(url_for('gestion_db.gestionar_data'))
    finally:
        if cursor is not None:
            cursor.close()

# Ruta para generar copia de seguridad en Excel
@gestion_db_bp.route("/backup_excel", methods=["POST"])
@requiere_super_admin
def backup_excel_route():
    response = generar_backup_excel()
    if not response:
        flash("Error desconocido al generar la copia de seguridad", "danger")
        return redirect(url_for('gestion_db.gestionar_data'))
    if isinstance(response, str) or getattr(response, "status_code", 200) != 200:
        return response
    flash("Copia de seguridad generada con éxito", "success")
    return response

    
  

# Ruta principal de gestión de datos
@gestion_db_bp.route("/gestionar_data", methods=["GET"])
@requiere_super_admin
def gestionar_data():
    messages = get_flashed_messages(with_categories=True)
    return render_template("gestionar_data.html", messages=messages)