from django.shortcuts import render
import pathlib
import xml.etree.ElementTree as ET
from django.http import HttpResponse, JsonResponse
from datetime import datetime

def agregar_addenda(request, factura_name):
    try:
        # Ruta del archivo XML guardado localmente
                # Obtener la ruta absoluta del proyecto
        proyecto_dir = pathlib.Path(__file__).resolve().parent

        # Construir la ruta al archivo XML al lado del proyecto
     #    file_name = f"Factura_{factura_name} (2).xml"  # Usar el nombre exacto que tienes
        file_path = proyecto_dir.parent / 'facturas_xml' / factura_name
        
        # Cargar el XML local
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except FileNotFoundError:
            return JsonResponse({"error": "Archivo XML no encontrado."}, status=404)

        # Namespace para el CFDI y Addenda
        cfdi_ns = "http://www.sat.gob.mx/cfd/4"
        eu_ns = "http://factura.envasesuniversales.com/addenda/eu"
        
        # Registrar namespaces
        ET.register_namespace("cfdi", cfdi_ns)
        ET.register_namespace("eu", eu_ns)
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

        # Obtener los valores del XML del comprobante
        comprobante = root.attrib  # el nodo raíz suele ser <cfdi:Comprobante>
        
        total = float(comprobante.get('Total') or "0.0")  # Total de la factura
        moneda = comprobante.get('Moneda')  # Moneda de la factura
        tipocambio = float(comprobante.get('TipoCambio') or "1.0")  # Tipo de cambio
        subtotal = float(comprobante.get('SubTotal') or "0.0")  # Subtotal de la factura
        
        # Obtener los impuestos (si existen)
        impuestos_node = root.find('cfdi:Impuestos', namespaces={'cfdi': cfdi_ns})
        total_impuestos = float(impuestos_node.attrib.get('TotalImpuestosTrasladados') or "0.0")
        
        # Crear la estructura de la Addenda EU
        addenda = ET.Element(f"{{{cfdi_ns}}}Addenda")
        addenda_eu = ET.SubElement(
            addenda,
            f"{{{eu_ns}}}AddendaEU",
            attrib={
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": f"{eu_ns} {eu_ns}/EU_Addenda.xsd",
                "xmlns:eu": eu_ns
            }
        )

        # Crear el bloque TipoFactura
        tipo_factura = ET.SubElement(addenda_eu, f"{{{eu_ns}}}TipoFactura")
        ET.SubElement(tipo_factura, f"{{{eu_ns}}}IdFactura").text = "Factura"
        ET.SubElement(tipo_factura, f"{{{eu_ns}}}Version").text = "1.0"
        ET.SubElement(tipo_factura, f"{{{eu_ns}}}FechaMensaje").text = datetime.now().strftime("%Y-%m-%d")
        
        # Crear el bloque TipoTransaccion
        tipo_trans = ET.SubElement(addenda_eu, f"{{{eu_ns}}}TipoTransaccion")
        ET.SubElement(tipo_trans, f"{{{eu_ns}}}IdTransaccion").text = "Con_Pedido"
        ET.SubElement(tipo_trans, f"{{{eu_ns}}}Transaccion").text = "3963"  # Personalizar según tu transacción
        
        # Crear la sección OrdenesCompra
        ordenes = ET.SubElement(addenda_eu, f"{{{eu_ns}}}OrdenesCompra")
        secuencia = ET.SubElement(ordenes, f"{{{eu_ns}}}Secuencia", attrib={"consec": "1"})
        ET.SubElement(secuencia, f"{{{eu_ns}}}IdPedido").text = "5467892356"  # Personalizar según tu lógica
        entrada_almacen = ET.SubElement(secuencia, f"{{{eu_ns}}}EntradaAlmacen")
        ET.SubElement(entrada_almacen, f"{{{eu_ns}}}Albaran").text = "12345645"  # Personalizar

        # Crear la sección Moneda
        moneda_eu = ET.SubElement(addenda_eu, f"{{{eu_ns}}}Moneda")
        ET.SubElement(moneda_eu, f"{{{eu_ns}}}MonedaCve").text = moneda
        ET.SubElement(moneda_eu, f"{{{eu_ns}}}TipoCambio").text = f"{tipocambio:.6f}"
        ET.SubElement(moneda_eu, f"{{{eu_ns}}}SubtotalM").text = f"{subtotal:.6f}"
        ET.SubElement(moneda_eu, f"{{{eu_ns}}}TotalM").text = f"{total:.6f}"
        ET.SubElement(moneda_eu, f"{{{eu_ns}}}ImpuestoM").text = f"{total_impuestos:.6f}"

        # Añadir la Addenda al nodo root del XML
        root.append(addenda)

        # Guardar el XML modificado
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

        # Generar la respuesta con el XML modificado
        modified_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        
        # Crear respuesta HTTP con el XML generado para la descarga
        response = HttpResponse(modified_xml, content_type="application/xml")
        response["Content-Disposition"] = f"attachment; filename=factura_{factura_name}__addenda.xml"
        return response

    except Exception as e:
        return JsonResponse({"error": f"Error al procesar la solicitud: {str(e)}"}, status=500)
