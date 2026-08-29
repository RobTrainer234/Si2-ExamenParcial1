# Arquitectura inicial

FashionStore utiliza un monolito modular con separación por capas:

`Router -> Service -> Repository -> PostgreSQL`

Los clientes Angular y Flutter consumen exclusivamente la API REST versionada
de FastAPI. Las integraciones futuras de pagos, IA y realidad aumentada se
mantendrán como módulos independientes.
