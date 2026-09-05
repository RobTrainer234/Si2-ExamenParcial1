# Aclaración de CU1 y CU2

## CU1: Registrar Cliente

El cliente proporciona sus datos personales y credenciales. El sistema valida
el formato, comprueba que el correo no exista, crea la cuenta con rol `CLIENT`
y devuelve una sesión inicial.

Las credenciales incorrectas no forman parte del registro; corresponden al
CU2. El correo duplicado y los datos inválidos son excepciones de CU1.

## CU2: Gestionar Inicio y Cierre de Sesión

El usuario registrado proporciona sus credenciales. El sistema valida el
usuario activo, identifica su rol y permisos, crea una sesión con access token
y refresh token, y habilita las operaciones permitidas.

El cierre requiere el `refresh_token` de la sesión. Un token inexistente,
revocado o inválido se rechaza y un token válido se revoca, invalidando también
el access token asociado.
