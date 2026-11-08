import docx

doc = docx.Document(r"c:\ProyectoSi2_TiendaRopa\docsegundoparcialSI2.docx")
body = doc._body._element

start_node = None # The first node to delete: P1393 ('4.4. Desarrollo de los módulos del sistema')
end_node = None   # The target before which to insert and where deletion stops: P1417 ('Capítulo 5: Pruebas y Resultados')

for child in body:
    if child.tag.endswith('p'):
        t = ''.join(child.itertext()).strip()
        if t.startswith("4.4. Desarrollo de los módulos") or "4.4. Desarrollo de los módulos" in t:
            if start_node is None:
                start_node = child
        elif (t.startswith("Capítulo 5:") or t.startswith("Capitulo 5:")) and start_node is not None:
            end_node = child
            break

print("start_node found:", start_node is not None)
print("end_node found:", end_node is not None)

# Traverse from start_node to end_node
cur = start_node
to_remove = []
while cur is not None and cur != end_node:
    to_remove.append(cur)
    cur = cur.getnext()

print("Total elements to replace:", len(to_remove))
