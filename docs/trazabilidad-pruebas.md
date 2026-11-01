# Trazabilidad y verificación de SalaMandra

- Actualización: 1 de noviembre de 2026.
- Relaciones: [requisitos](sesion-06-requisitos.md), [casos de uso](sesion-07-modelos.md), [arquitectura](arquitectura.md), [sesión 12 y CI](sesion-12-arquitectura.md).

## 1. Alcance y resultado comprobado

La última ejecución local completa del código revisado finalizó con **104 passed in 166.99s** (1 de noviembre de 2026). Es evidencia local de esa revisión, no una ejecución nueva de GitHub Actions ni una garantía para versiones posteriores.

| Marca actual de pytest | Casos |
|---|---:|
| `unit` | 83 |
| `integration` | 16 |
| `e2e` | 5 |
| **Total** | **104** |

El conteo incluye cada combinación parametrizada como caso separado. Los números en comentarios antiguos de los tests no constituyen el inventario actual.

**Límite de la clasificación:** `tests/conftest.py` asigna automáticamente `unit` a toda prueba sin marca `integration` o `e2e`. Las cantidades describen las marcas actuales, no certifican 83 pruebas unitarias aisladas: varias utilizan ORM y vistas. Las `e2e` actuales usan el cliente HTTP de Django, sin navegador real ni JavaScript. No se declara una distribución de 80/15/5 que el repositorio no posee.

## 2. Requisito, caso, presentación, lógica y comprobación

Las vistas son el punto de entrada habitual de la interfaz, aunque algunos tests de esta tabla invocan directamente el servicio. La asociación no implica que todos prueben el HTML.

| Funcionalidad | Caso / requisito | Vista relacionada | Lógica | Test representativo |
|---|---|---|---|---|
| Registro | RES-CU-13 / soporte | `register_view` | `register_student_account` | `test_registro_conserva_validacion_y_no_reemplaza_contrasena` |
| Login y logout | RES-CU-14 / soporte | `login_view, logout_view, dashboard_view` | `authenticate_user` | `test_login_y_logout_del_administrador` |
| Identidad al crear | RES-CU-01 / RES-RF-06,16 | `student_panel_view` | `create_student_reservation → create_reservation` | `test_panel_y_reserva_usan_la_identidad_de_la_sesion` |
| Consecutividad | RES-CU-01 / RES-RF-08 | `student_panel_view` | `_validar_sin_bloques_consecutivos` | `test_bloques_consecutivos_y_separados` |
| Calendario | RES-CU-01 / RES-RF-08 | `student_panel_view` | `_validar_dia_habil, _es_dia_habilitado` | `test_fin_de_semana_y_feriados` |
| Limpieza | RES-CU-01 / RES-RF-08 | `student_panel_view` | `_validar_intervalo_limpieza` | `test_intervalo_de_limpieza` |
| Modificar reserva propia | RES-CU-02 / RES-RF-01,10 | `modify_reservation_view` | `modify_student_reservation → modify_reservation` | `test_modificar_reserva_cambia_sala_y_conserva_la_misma_fila` |
| Límite de modificación | RES-CU-02 / RES-RF-01 | `modify_reservation_view` | `_validar_plazo_modificacion` | `test_modificacion_exige_60_minutos_y_conserva_reserva_original` |
| Cancelar y sancionar | RES-CU-03 / RES-RF-02,15,24 | `cancel_reservation_view` | `cancel_reservation, _registrar_sancion_por_cancelacion` | `test_cancelacion_tardia_aplica_sancion_escalar` |
| Advertencia de cancelación | RES-CU-03 / RES-RF-24 | `cancel_reservation_view` | `cancel_reservation` | `test_cancelacion_desde_el_panel_muestra_resultado` |
| Crear para otro titular | RES-CU-04 / RES-RF-05,18 | `operator_panel_view` | `create_reservation` | `test_operante_reserva_para_solicitante_y_audita_actor` |
| Modificar y cancelar asistidas | RES-CU-05,06 / RES-RF-01,18,19 | `operator_panel_view` | `modify_reservation, cancel_reservation` | `test_operante_modifica_y_cancela_reserva_ajena` |
| Estudiante sin registro | RES-CU-04,05,06 / RES-RF-05,18 | `operator_panel_view` | `get_operator_student y servicios de reserva` | `test_servicios_operante_rechazan_solicitante_sin_cuenta` |
| Mantenimiento del Operante | RES-CU-07 / RES-RF-03,21 | `operator_panel_view, operator_unblock_room_view` | `block_room_schedule_for_maintenance, unblock_room_schedule_from_maintenance` | `test_operante_gestiona_mantenimiento_sin_sancionar` |
| Consultar y reconocer avisos | RES-CU-08 / RES-RF-07,22 | `student_panel_view, mark_notification_read_view` | `get_student_panel, mark_notification_as_read` | `test_panel_muestra_aviso_y_permite_marcarlo_como_leido` |
| Modificación administrativa | RES-CU-09 / RES-RF-01,13 | `modify_reservation_view` | `modify_reservation` | `test_admin_mueve_reserva_ajena_ya_iniciada_desde_la_interfaz` |
| Mantenimiento administrativo | RES-CU-10 / RES-RF-03,17 | `block_room_view` | `block_room_schedule_for_maintenance` | `test_bloqueo_exitoso_cambia_reserva_sin_sancionar` |
| Rechazo de doble bloqueo | RES-CU-10 / RES-RF-03 | `block_room_view` | `block_room_schedule_for_maintenance` | `test_doble_bloqueo_no_crea_otro_registro` |
| Sin permiso de mantenimiento | RES-CU-10 / RES-RF-13 | `block_room_view` | `block_room_schedule_for_maintenance` | `test_solicitante_sin_permiso_no_modifica_el_horario` |
| Cancelación administrativa | RES-CU-11 / RES-RF-20 | `admin_cancellations_view, admin_cancel_reservation_view` | `get_admin_cancellable_reservations, cancel_reservation` | `test_administrador_lista_y_cancela_reservas_sin_sancion` |
| Sanción manual | RES-CU-12 / RES-RF-14 | `apply_sanction_view` | `apply_manual_sanction, calcular_fecha_fin_sancion` | `test_aplica_sancion_manual_con_motivo_y_duracion` |
| Reinicio general | RES-CU-12 / RES-RF-15 | `clear_sanctions_view` | `clear_all_sanctions, contar_faltas` | `test_reinicio_manual_corta_contador_sin_perder_faltas_vencidas` |
| Retiro individual | RES-CU-12 / RES-RF-23 | `withdraw_sanction_view` | `withdraw_sanction` | `test_retiro_individual_preserva_contador_y_rechaza_repeticion` |
| Integridad de transacción | RES-RT-01 / auditoría | `student_panel_view` | `create_student_reservation, transaction.atomic` | `test_fallo_auditoria_al_crear_revierte_la_reserva` |
| Unicidad persistente | RES-RF-16 | `No requiere vista` | `Reserva.Meta.constraints` | `test_restriccion_bd_por_fecha_y_estado` |

## 3. Inventario de los 104 casos

Los puntos de entrada siguientes identifican llamadas directas a servicios o rutas utilizadas en el cuerpo del test. Las rutas llevan a la vista declarada en los `urls.py`. Las fixtures pueden preparar usuarios, autenticar y crear datos adicionales; por ello esta columna no es una lista exhaustiva de todas las funciones transitivas. Cuando no aparece un servicio o ruta, la prueba puede comprobar directamente modelos, restricciones o migraciones.

### [tests/sesion12/test_flujo_mantenimiento.py](../tests/sesion12/test_flujo_mantenimiento.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_bloqueo_exitoso_cambia_reserva_sin_sancionar` | `integration` | `services.block_room_schedule_for_maintenance` |
| `test_doble_bloqueo_no_crea_otro_registro` | `integration` | `services.block_room_schedule_for_maintenance` |
| `test_solicitante_sin_permiso_no_modifica_el_horario` | `integration` | `services.block_room_schedule_for_maintenance` |

### [tests/test_auditoria_roles.py](../tests/test_auditoria_roles.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_historial_crear_modificar_cancelar_conserva_titular` | `unit` | `services.cancel_reservation`<br/>`services.create_student_reservation`<br/>`services.modify_student_reservation` |
| `test_fallo_auditoria_al_crear_revierte_la_reserva` | `integration` | `services.create_student_reservation` |
| `test_cancelacion_repetida_no_duplica_historial_ni_sancion` | `unit` | `services.cancel_reservation`<br/>`services.create_student_reservation` |
| `test_mantenimiento_registra_administrador_y_no_sanciona` | `unit` | `services.block_room_schedule_for_maintenance`<br/>`services.create_student_reservation` |
| `test_solicitante_no_puede_sancionar_manualmente` | `unit` | `gestion_sanciones.apply_manual_sanction` |
| `test_bd_rechaza_origen_aplicador_incoherentes` | `unit` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |
| `test_modelo_valida_rol_del_aplicador` | `unit` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |
| `test_rol_unico_y_catalogo_restringido` | `unit` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |
| `test_registro_no_cambia_rol_de_administrador` | `unit` | `register_student_account` |
| `test_auditoria_rechaza_acciones_fuera_del_catalogo` | `unit` | `services.create_student_reservation` |

### [tests/test_cancelar_reserva.py](../tests/test_cancelar_reserva.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_cancela_exactamente_60_minutos_antes_sin_sancion` | `unit` | `services.cancel_reservation`<br/>`services.create_student_reservation` |
| `test_cancelacion_tardia_aplica_sancion_escalar[0-74-24]` | `unit` | `services.cancel_reservation` |
| `test_cancelacion_tardia_aplica_sancion_escalar[2-76-168]` | `unit` | `services.cancel_reservation` |
| `test_cancelacion_tardia_aplica_sancion_escalar[3-77-None]` | `unit` | `services.cancel_reservation` |
| `test_no_cancela_una_reserva_que_ya_comenzo` | `unit` | `services.cancel_reservation` |
| `test_solicitante_no_puede_cancelar_reserva_ajena` | `unit` | `services.cancel_reservation` |
| `test_operador_cancela_sin_sancionar_y_notifica_al_titular` | `integration` | `services.cancel_reservation` |
| `test_cancelacion_desde_el_panel_muestra_resultado` | `unit` | `ruta cancel_reservation`<br/>`ruta student_panel` |
| `test_administrador_lista_y_cancela_reservas_sin_sancion` | `unit` | `ruta admin_cancel_reservation`<br/>`ruta admin_cancellations`<br/>`ruta login`<br/>`ruta logout` |

### [tests/test_cuentas.py](../tests/test_cuentas.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_login_y_logout_del_administrador` | `e2e` | `ruta dashboard`<br/>`ruta login`<br/>`ruta logout` |
| `test_login_solicitante_y_acceso_restringido` | `e2e` | `ruta block_room`<br/>`ruta dashboard`<br/>`ruta login`<br/>`ruta student_panel` |
| `test_registro_conserva_validacion_y_no_reemplaza_contrasena` | `e2e` | `ruta login`<br/>`ruta registro` |

### [tests/test_gestion_sala_deshabilitada.py](../tests/test_gestion_sala_deshabilitada.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_administrador_no_puede_abrir_ni_enviar_la_gestion_de_salas` | `unit` | `ruta dashboard`<br/>`ruta gestion_salas`<br/>`ruta login` |
| `test_servicios_de_gestion_tambien_rechazan_las_altas_y_retiros` | `unit` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |

### [tests/test_gestion_sanciones.py](../tests/test_gestion_sanciones.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_aplica_sancion_manual_con_motivo_y_duracion` | `unit` | `gestion_sanciones.apply_manual_sanction`<br/>`gestion_sanciones.calcular_fecha_fin_sancion` |
| `test_sancion_manual_de_semestre_termina_en_el_proximo_corte` | `unit` | `gestion_sanciones.apply_manual_sanction` |
| `test_listado_muestra_solo_la_sancion_vigente` | `unit` | `gestion_sanciones.get_solicitantes` |
| `test_sancion_manual_nueva_reemplaza_la_vigente_sin_borrar_historial` | `unit` | `gestion_sanciones.apply_manual_sanction`<br/>`gestion_sanciones.sanciones_vigentes`<br/>`gestion_sanciones.sanciones_vigentes(segunda_fecha).values_list` |
| `test_sancion_automatica_nueva_reemplaza_cualquier_sancion_vigente` | `integration` | `gestion_sanciones.apply_manual_sanction`<br/>`gestion_sanciones.sanciones_vigentes`<br/>`gestion_sanciones.sanciones_vigentes(inicio + timedelta(minutes=2)).values_list`<br/>`services._registrar_sancion_por_cancelacion` |
| `test_reinicio_manual_conserva_historial_y_registra_retiro` | `unit` | `gestion_sanciones.clear_all_sanctions`<br/>`gestion_sanciones.sanciones_vigentes`<br/>`gestion_sanciones.sanciones_vigentes(timezone.localtime()).exists` |
| `test_desactivar_cuenta_cierra_sesion_e_impide_login` | `unit` | `authenticate_user`<br/>`gestion_sanciones.set_student_active_status`<br/>`ruta login`<br/>`ruta logout`<br/>`ruta student_panel` |
| `test_pantalla_administrativa_procesa_sancion_estado_y_reinicio` | `unit` | `ruta apply_sanction`<br/>`ruta change_student_status`<br/>`ruta clear_sanctions`<br/>`ruta sanctions_admin` |
| `test_solicitante_no_puede_administrar_sanciones` | `unit` | `ruta clear_sanctions`<br/>`ruta login`<br/>`ruta logout`<br/>`ruta sanctions_admin` |
| `test_semestre_libera_y_reinicia_sin_borrar` | `unit` | `gestion_sanciones.contar_faltas`<br/>`gestion_sanciones.sanciones_vigentes`<br/>`gestion_sanciones.sanciones_vigentes(anterior).exists`<br/>`gestion_sanciones.sanciones_vigentes(frontera).exists`<br/>`services._registrar_sancion_por_cancelacion`<br/>`services._validar_sin_sancion` |
| `test_reinicio_manual_corta_contador_sin_perder_faltas_vencidas` | `unit` | `gestion_sanciones.clear_all_sanctions`<br/>`gestion_sanciones.contar_faltas`<br/>`services._registrar_sancion_por_cancelacion`<br/>`services._validar_sin_sancion` |
| `test_retiro_individual_preserva_contador_y_rechaza_repeticion` | `unit` | `gestion_sanciones.contar_faltas`<br/>`gestion_sanciones.get_solicitantes`<br/>`gestion_sanciones.withdraw_sanction`<br/>`services._registrar_sancion_por_cancelacion` |
| `test_retiro_exige_post_y_conserva_registro` | `unit` | `gestion_sanciones.apply_manual_sanction`<br/>`ruta withdraw_sanction` |

### [tests/test_migracion_catalogo_sanciones.py](../tests/test_migracion_catalogo_sanciones.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_migracion_consolida_tipos_sin_borrar_sanciones` | `integration` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |
| `test_migracion_corrige_duracion_y_fecha_fin_del_semestre` | `integration` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |

### [tests/test_notificaciones.py](../tests/test_notificaciones.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_mantenimiento_crea_aviso_persistente` | `unit` | `services.block_room_schedule_for_maintenance` |
| `test_cancelacion_de_gestion_notifica_al_titular` | `unit` | `services.cancel_reservation` |
| `test_cancelacion_propia_no_crea_aviso` | `unit` | `services.cancel_reservation` |
| `test_modificacion_de_gestion_notifica_origen_y_destino` | `integration` | `services.modify_reservation` |
| `test_cada_modificacion_de_gestion_conserva_su_notificacion` | `unit` | `services.modify_reservation` |
| `test_panel_muestra_aviso_y_permite_marcarlo_como_leido` | `unit` | `ruta mark_notification_read`<br/>`ruta student_panel` |
| `test_estudiante_no_puede_marcar_aviso_ajeno` | `unit` | `ruta mark_notification_read` |

### [tests/test_panel_operante.py](../tests/test_panel_operante.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_login_operante_llega_a_su_panel` | `unit` | `ruta dashboard`<br/>`ruta operator_panel` |
| `test_panel_renderiza_cada_apartado` | `unit` | `ruta operator_panel` |
| `test_operante_reserva_para_solicitante_y_audita_actor` | `unit` | `ruta operator_panel` |
| `test_operante_modifica_y_cancela_reserva_ajena` | `e2e` | `services.create_reservation`<br/>`ruta operator_panel` |
| `test_operante_gestiona_mantenimiento_sin_sancionar` | `unit` | `services.create_reservation`<br/>`ruta operator_panel`<br/>`ruta operator_unblock_room` |
| `test_operante_no_accede_a_sanciones_ni_gestion_de_horarios` | `unit` | `ruta apply_sanction`<br/>`ruta gestion_salas`<br/>`ruta sanctions_admin` |
| `test_panel_operante_rechaza_solicitante_sin_cuenta[reservar]` | `unit` | `ruta operator_panel` |
| `test_panel_operante_rechaza_solicitante_sin_cuenta[modificar]` | `unit` | `ruta operator_panel` |
| `test_panel_operante_rechaza_solicitante_sin_cuenta[cancelar]` | `unit` | `ruta operator_panel` |
| `test_servicios_operante_rechazan_solicitante_sin_cuenta[reservar]` | `unit` | `services.cancel_reservation`<br/>`services.create_reservation`<br/>`services.modify_reservation` |
| `test_servicios_operante_rechazan_solicitante_sin_cuenta[modificar]` | `unit` | `services.cancel_reservation`<br/>`services.create_reservation`<br/>`services.modify_reservation` |
| `test_servicios_operante_rechazan_solicitante_sin_cuenta[cancelar]` | `unit` | `services.cancel_reservation`<br/>`services.create_reservation`<br/>`services.modify_reservation` |
| `test_solicitante_no_accede_al_panel_operante` | `unit` | `ruta login`<br/>`ruta logout`<br/>`ruta operator_panel` |

### [tests/test_panel_solicitante.py](../tests/test_panel_solicitante.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_panel_y_reserva_usan_la_identidad_de_la_sesion` | `e2e` | `ruta student_panel` |
| `test_mantenimiento_cancela_y_rechaza_nueva_reserva` | `unit` | `services.block_room_schedule_for_maintenance`<br/>`services.create_student_reservation` |
| `test_bloques_consecutivos_y_separados` | `unit` | `services.create_student_reservation` |
| `test_restriccion_bd_por_fecha_y_estado` | `unit` | `services.create_student_reservation` |
| `test_sancion_permite_consultar_pero_no_reservar` | `unit` | `services.create_student_reservation`<br/>`ruta student_panel` |
| `test_fin_de_semana_y_feriados` | `unit` | `services.create_student_reservation` |
| `test_bloque_finalizado_se_oculta_y_se_rechaza` | `unit` | `services.create_student_reservation`<br/>`services.get_student_panel` |
| `test_intervalo_de_limpieza` | `unit` | `services.create_student_reservation` |
| `test_anonimo_no_puede_reservar` | `unit` | `ruta login`<br/>`ruta student_panel` |
| `test_dia_no_habilitado_oculta_salas_y_formulario` | `unit` | `ruta student_panel` |
| `test_modificar_reserva_cambia_sala_y_conserva_la_misma_fila` | `unit` | `services.create_student_reservation`<br/>`ruta modify_reservation`<br/>`ruta student_panel` |
| `test_modificacion_exige_60_minutos_y_conserva_reserva_original` | `unit` | `services.modify_student_reservation` |
| `test_destino_ocupado_no_libera_la_reserva_original` | `unit` | `services.create_student_reservation`<br/>`services.modify_student_reservation` |
| `test_modificacion_respeta_bloques_consecutivos` | `unit` | `services.create_student_reservation`<br/>`services.modify_student_reservation` |
| `test_no_se_puede_modificar_una_reserva_ajena` | `unit` | `services.create_student_reservation`<br/>`services.modify_student_reservation` |

### [tests/test_privilegios_administrador.py](../tests/test_privilegios_administrador.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_admin_reserva_para_si_mismo_bloques_consecutivos_y_mismo_bloque` | `unit` | `services.create_student_reservation` |
| `test_admin_modifica_reserva_iniciada_a_otro_bloque_y_operante_no` | `unit` | `services.modify_reservation`<br/>`ruta login`<br/>`ruta modify_reservation` |
| `test_modificacion_identica_se_rechaza_sin_auditoria_ni_aviso` | `unit` | `services.modify_reservation` |
| `test_admin_mueve_reserva_ajena_a_bloque_consecutivo_y_queda_como_actor` | `unit` | `services.modify_reservation` |
| `test_admin_cancela_reserva_iniciada_sin_sancion_y_notifica` | `unit` | `services.cancel_reservation` |
| `test_admin_mantenimiento_tras_inicio_y_operante_restringido` | `unit` | `services.block_room_schedule_for_maintenance` |
| `test_panel_admin_muestra_acciones_de_reserva_iniciada` | `unit` | `ruta admin_cancel_reservation`<br/>`ruta admin_cancellations`<br/>`ruta cancel_reservation`<br/>`ruta login`<br/>`ruta modify_reservation`<br/>`ruta student_panel` |
| `test_panel_admin_no_advierte_sancion_al_cancelar_reserva_propia` | `unit` | `ruta cancel_reservation`<br/>`ruta login`<br/>`ruta student_panel` |
| `test_admin_mueve_reserva_ajena_ya_iniciada_desde_la_interfaz` | `unit` | `ruta admin_cancellations`<br/>`ruta login`<br/>`ruta modify_reservation` |
| `test_formulario_admin_muestra_todos_los_bloques_de_reserva_futura` | `unit` | `ruta login`<br/>`ruta modify_reservation` |

### [tests/test_seed_data.py](../tests/test_seed_data.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_seed_data_carga_seis_salas_con_seis_horarios_sin_duplicar` | `integration` | `call_command` |
| `test_seed_data_precarga_los_16_alumnos_y_no_reemplaza_cuentas_registradas` | `integration` | `call_command`<br/>`register_student_account` |
| `test_seed_data_reset_funciona_con_todo_el_historial_nuevo` | `integration` | `call_command` |

### [tests/test_zona_horaria.py](../tests/test_zona_horaria.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_sqlite_guarda_datetime_en_hora_de_la_paz_y_django_conserva_instante` | `integration` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |
| `test_conversion_utc_a_la_paz_conserva_microsegundos_y_cambia_dia` | `unit` | `_a_hora_local` |

### [tests/tests_mantenimiento.py](../tests/tests_mantenimiento.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `TestBloqueoMantenimiento::test_administrador_puede_bloquear_un_horario_que_ya_comenzo` | `unit` | `services.block_room_schedule_for_maintenance` |
| `TestBloqueoMantenimiento::test_aislamiento_no_afecta_otras_salas_ni_horarios` | `unit` | `services.block_room_schedule_for_maintenance` |
| `TestBloqueoMantenimiento::test_sala_o_horario_inexistente` | `unit` | `services.block_room_schedule_for_maintenance` |
| `TestSalidaDeMantenimiento::test_administrador_vuelve_a_habilitar_horario` | `unit` | `services.block_room_schedule_for_maintenance`<br/>`services.unblock_room_schedule_from_maintenance` |
| `TestSalidaDeMantenimiento::test_no_permite_desbloquear_si_el_mantenimiento_ya_empezo` | `unit` | `services.block_room_schedule_for_maintenance`<br/>`services.unblock_room_schedule_from_maintenance` |
| `TestSalidaDeMantenimiento::test_estudiante_no_puede_sacar_horario_de_mantenimiento` | `unit` | `services.block_room_schedule_for_maintenance`<br/>`services.unblock_room_schedule_from_maintenance` |
| `TestSalidaDeMantenimiento::test_rechaza_habilitar_horario_que_no_esta_en_mantenimiento` | `unit` | `services.unblock_room_schedule_from_maintenance` |
| `TestSalidaDeMantenimiento::test_lista_activa_excluye_horario_despues_de_habilitarlo` | `unit` | `services.block_room_schedule_for_maintenance`<br/>`services.get_active_maintenance_blocks`<br/>`services.unblock_room_schedule_from_maintenance` |
| `TestSalidaDeMantenimiento::test_boton_de_interfaz_habilita_el_horario` | `unit` | `services.block_room_schedule_for_maintenance` |

### [tests/test_migracion_auditoria.py](../tests/test_migracion_auditoria.py)

| Caso de prueba | Marca | Entradas ejercitadas |
|---|---|---|
| `test_migra_roles_y_sanciones_sin_inventar_auditoria` | `integration` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |
| `test_migracion_rechaza_datos_ambiguos_sin_perderlos[roles_ambiguos]` | `integration` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |
| `test_migracion_rechaza_datos_ambiguos_sin_perderlos[sancion_sin_autor]` | `integration` | Modelos/ORM o migraciones, sin llamada directa a servicio o ruta en el cuerpo. |

## 4. Ejecución local y GitHub Actions

```bash
# Suite completa
python -m pytest -q

# Selección por marca actual
python -m pytest -m unit -q
python -m pytest -m integration -q
python -m pytest -m e2e -q

# Inventario, sin ejecutar los cuerpos de prueba
python -m pytest --collect-only -q

# Contrato específico usado en CI
python -m pytest tests/sesion12 -q --junitxml=evidencias/sesion12-junit.xml
```

El workflow `.github/workflows/ci-sesion12.yml` ejecuta **solo tres pruebas** de `tests/sesion12/`, no la suite completa. Se activa en push, pull request o ejecución manual. Usa Ubuntu y Python 3.13, instala `requirements.txt` y conserva el reporte JUnit. Si tiene éxito en `main`, también archiva el código fuente como candidato ZIP. Esto no despliega la aplicación.

Las ejecuciones históricas enlazadas en sesión 12 corresponden a sus commits y no sustituyen una ejecución actual sobre la versión revisada. Los tres tests de CI y el workflow se conservaron sin cambios al eliminar duplicaciones de la suite general.

## 5. Interpretación y mantenimiento

- Las pruebas de sesión 12 mantienen los casos esenciales de éxito, doble bloqueo y falta de permisos. Las comprobaciones generales de bitácora y reservas futuras se conservaron al consolidar duplicados.
- Una prueba HTTP y otra de servicio pueden cubrir la misma regla desde entradas distintas y no son necesariamente redundantes.
- Comprobar una restricción de base de datos no demuestra por sí solo el comportamiento de dos peticiones concurrentes reales.
- El inventario incluye pruebas de gestión deshabilitada y estado de cuentas porque existen en el sistema, aunque la sesión 20 omita el recorrido de activar/desactivar.
- El bloqueo del Operante en `/salas/`, el formato exacto del mensaje de vencimiento y el retiro simultáneo de varias sanciones tuvieron comprobaciones puntuales aisladas durante la revisión. No se cuentan como casos adicionales en esta suite si no están persistidos como tests.
- Al cambiar requisitos, funciones, parámetros o marcas, actualizar esta matriz, volver a recopilar los casos y registrar el nuevo resultado. No eliminar casos distintos para forzar una cantidad prefijada.
