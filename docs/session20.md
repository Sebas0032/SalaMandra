# Sesión 20 — Recorrido de registro e inicio de sesión

## Registrar cuenta

```mermaid
flowchart LR
    A["Persona<br/>Ingresa código, correo y contraseña"]
    B["Presentación: Registrar<br/>Recoge los datos del formulario"]
    C["Lógica<br/>register_student_account(código, correo, contraseña)<br/>Valida que el código exista, que el usuario esté activo,<br/>que el correo corresponda y que no tenga cuenta"]
    D["Resultado<br/>Si acepta crea la cuenta como Solicitante y dirige al login<br/>Si falla este muestra el motivo del rechazo"]

    A --> B
    B --> C
    C --> D
```

La presentación recoge los datos, la lógica aplica las reglas de registro y la presentación comunica si la cuenta fue creada o rechazada.

## Iniciar sesión

```mermaid
flowchart LR
    A["Persona<br/>Ingresa código y contraseña"]
    B["Presentación: Iniciar sesión<br/>Recoge las credenciales"]
    C["Lógica<br/>authenticate_user(código (identificador), contraseña)<br/>Valida que el usuario este activo, contraseña y rol permitido"]
    D["Resultado<br/>Si acepta entonces inicia sesión y dirige al panel correspondiente que se debe mostrar<br/>Si falla se informa que el código o contraseña estan incorrectos, o cuenta no habilitada"]

    A --> B
    B --> C
    C --> D
```

La presentación recoge las credenciales, la lógica comprueba la cuenta y la presentación comunica el resultado o dirige al usuario a su panel.
