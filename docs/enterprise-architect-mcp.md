# Enterprise Architect MCP

## Purpose

FashionStore uses a local MCP bridge to create and inspect UML diagrams in Sparx Enterprise Architect through its Windows Automation Interface.

## Prerequisites

- Windows.
- Sparx Enterprise Architect installed. The current machine has EA Trial installed under `C:\Program Files (x86)\Sparx Systems\EA Trial\EA.exe`.
- The bridge virtual environment at `C:\Proyecto-GestionEventos\plataforma-gestion-eventos\herramientas\mcp-enterprise-architect\.venv` with `mcp` and `pywin32` installed.
- A model file created and saved by Enterprise Architect at `docs/uml/FashioStore/FashionStore.eap`.

## First-time model setup

1. Open Enterprise Architect.
2. Create a new project/model.
3. Save it as:

   `C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap`

4. Close the model in EA before allowing the MCP bridge to open it.
5. Reload the MCP client so it reads `antigravity.jsonc`.

The project configuration supplies `EA_MODEL_PATH` with this path. The bridge intentionally does not create a model automatically and does not open a guessed file.

## Configured MCP server

The root `antigravity.jsonc` registers `enterprise-architect` using the existing bridge:

- `ea_status`
- `ea_open_model`
- `ea_close_model`
- `ea_list_packages`
- `ea_list_elements`
- `ea_get_element`
- `ea_create_class_diagram`
- `ea_create_sequence_diagram`
- `ea_create_use_case_diagram`
- `ea_create_activity_diagram`
- `ea_create_component_diagram`
- `ea_create_deployment_diagram`
- `ea_create_state_diagram`
- `ea_create_object_diagram`
- `ea_create_communication_diagram`
- `ea_create_package_diagram`
- `ea_export_diagram`

The bridge uses a single COM worker thread and validates diagram specifications before writing. Create a backup of `FashionStore.eap` before bulk diagram changes.

## Supported UML coverage

| Tool | Native EA diagram | Main input |
| --- | --- | --- |
| `ea_create_use_case_diagram` | Use Case | Actors, use cases, associations/include/extend |
| `ea_create_class_diagram` | Class | Classes, attributes, methods, relationships |
| `ea_create_sequence_diagram` | Sequence | Participants and ordered messages |
| `ea_create_activity_diagram` | Activity | Actions, decisions, initial/final nodes, control flows |
| `ea_create_component_diagram` | Component | Components, interfaces, dependencies |
| `ea_create_deployment_diagram` | Deployment | Nodes, devices, artifacts, deployment paths |
| `ea_create_state_diagram` | Statechart | States, initial/final nodes, transitions |
| `ea_create_object_diagram` | Object | Instances and links |
| `ea_create_communication_diagram` | Communication | Participants and numbered messages |
| `ea_create_package_diagram` | Package | Nested UML package organization |

All creation tools write native EA elements and connectors instead of drawing a flat image. `ea_export_diagram` can then export the resulting diagram for academic documentation.

## Recommended first operation

After the model exists, ask the MCP client to run `ea_status`, then `ea_open_model` with the configured model path. List packages before creating a diagram. Use a dedicated package such as `FashionStore / UML / Architecture` for generated diagrams.

## Scope and limitations

- The bridge creates native class, sequence, use-case, activity, component, deployment, state, object, communication, and package-organization diagrams.
- The current Pi session does not automatically load local command-based MCP definitions; `antigravity.jsonc` is for the compatible MCP client. Reload that client to expose the tools.
- `drawio-mcp` is referenced in the configuration but is not installed on PATH; it is not required for Enterprise Architect diagrams.
