import ExcelJS from 'exceljs'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

const downloadBlob = (blob, fileName) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(link)
}

export const exportHostsToExcel = async (hostsToExport) => {
  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet('Escaneo de Red')

  worksheet.columns = [
    { header: 'IP', key: 'ip', width: 15 },
    { header: 'Nombre de host', key: 'hostname', width: 20 },
    { header: 'Apodo', key: 'nickname', width: 20 },
    { header: 'MAC', key: 'mac', width: 18 },
    { header: 'Fabricante', key: 'vendor', width: 20 },
    { header: 'SO', key: 'os', width: 15 },
    { header: 'Estado', key: 'status', width: 10 },
    { header: 'Latencia (ms)', key: 'latency', width: 12 },
    { header: 'Última vez visto', key: 'lastSeen', width: 20 },
    { header: 'Puertos', key: 'ports', width: 30 },
    { header: 'Servicios', key: 'services', width: 30 },
  ]

  hostsToExport.forEach((host) => {
    worksheet.addRow({
      ip: host.ip,
      hostname: host.hostname || 'N/A',
      nickname: host.nickname || '',
      mac: host.mac || 'N/A',
      vendor: host.vendor || 'N/A',
      os: host.os_name || 'N/A',
      status: host.status,
      latency: host.latency_ms || 'N/A',
      lastSeen: host.last_seen ? new Date(host.last_seen).toLocaleString() : 'N/A',
      ports: (host.ports || []).map((port) => `${port.port}/${port.protocol}`).join(', '),
      services: (host.services || []).map((service) => service.service).join(', '),
    })
  })

  worksheet.getRow(1).font = { bold: true }
  worksheet.getRow(1).fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FF4CAF50' },
  }

  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })

  downloadBlob(blob, `ite_scan_${Date.now()}.xlsx`)
}

export const exportHostsToPNG = async (hostsToExport) => {
  const container = document.createElement('div')
  container.style.position = 'absolute'
  container.style.left = '-9999px'
  container.style.width = '1200px'
  container.style.padding = '40px'
  container.style.backgroundColor = '#0f172a'
  container.style.fontFamily = 'Arial, sans-serif'

  const header = document.createElement('div')
  header.style.marginBottom = '30px'
  header.innerHTML = `
    <h1 style="color: #67e8f9; font-size: 32px; margin: 0 0 10px 0;">ITE Scan</h1>
    <p style="color: #94a3b8; font-size: 14px; margin: 0;">Generated: ${new Date().toLocaleString()}</p>
    <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0 0;">Total Hosts: ${hostsToExport.length}</p>
  `
  container.appendChild(header)

  const table = document.createElement('table')
  table.style.width = '100%'
  table.style.borderCollapse = 'collapse'
  table.style.fontSize = '12px'

  const thead = document.createElement('thead')
  thead.innerHTML = `
    <tr style="background: #1e293b;">
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">IP Address</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">Hostname</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">Apodo</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">MAC</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">Vendor</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">OS</th>
      <th style="padding: 12px; text-align: center; color: #67e8f9; border: 1px solid #475569;">Status</th>
      <th style="padding: 12px; text-align: center; color: #67e8f9; border: 1px solid #475569;">Ports</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">Last Seen</th>
    </tr>
  `
  table.appendChild(thead)

  const tbody = document.createElement('tbody')
  hostsToExport.forEach((host, index) => {
    const row = document.createElement('tr')
    row.style.background = index % 2 === 0 ? '#0f172a' : '#1e293b'

    const statusColor = host.status === 'up' ? '#22c55e' : '#ef4444'
    const statusText = (host.status || 'unknown').toUpperCase()

    row.innerHTML = `
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.ip}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.hostname || 'N/A'}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.nickname || ''}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.mac || 'N/A'}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.vendor || 'N/A'}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.os_name || 'N/A'}</td>
      <td style="padding: 10px; text-align: center; border: 1px solid #475569;">
        <span style="display: inline-block; padding: 4px 12px; background: ${statusColor}; color: white; border-radius: 4px; font-weight: bold;">${statusText}</span>
      </td>
      <td style="padding: 10px; color: #e2e8f0; text-align: center; border: 1px solid #475569;">${host.ports?.length || 0}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.last_seen ? new Date(host.last_seen).toLocaleString() : 'N/A'}</td>
    `

    tbody.appendChild(row)
  })
  table.appendChild(tbody)
  container.appendChild(table)

  const footer = document.createElement('div')
  footer.style.marginTop = '30px'
  footer.style.textAlign = 'center'
  footer.innerHTML = '<p style="color: #94a3b8; font-size: 12px; margin: 0;">ITE Scan Dashboard</p>'
  container.appendChild(footer)

  document.body.appendChild(container)

  try {
    const canvas = await html2canvas(container, {
      scale: 2,
      backgroundColor: '#0f172a',
      logging: false,
      width: 1200,
      windowWidth: 1200,
    })

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob((blobResult) => {
        if (blobResult) resolve(blobResult)
        else reject(new Error('No se pudo generar la imagen PNG'))
      })
    })

    downloadBlob(blob, `ite_scan_${Date.now()}.png`)
  } finally {
    document.body.removeChild(container)
  }
}

export const exportHostsToPDF = async (hostsToExport) => {
  const pdf = new jsPDF('l', 'mm', 'a4')

  pdf.setFontSize(20)
  pdf.setTextColor(34, 211, 238)
  pdf.setFont(undefined, 'bold')
  pdf.text('Reporte de Escaneo de Red', 14, 15)

  pdf.setDrawColor(34, 211, 238)
  pdf.setLineWidth(0.5)
  pdf.line(14, 18, 280, 18)

  pdf.setFontSize(10)
  pdf.setTextColor(100)
  pdf.setFont(undefined, 'normal')
  pdf.text(`Fecha: ${new Date().toLocaleDateString()}`, 14, 25)
  pdf.text(`Hora: ${new Date().toLocaleTimeString()}`, 14, 30)
  pdf.text(`Total de Hosts: ${hostsToExport.length}`, 100, 25)
  pdf.text(`Hosts Activos: ${hostsToExport.filter((host) => host.status === 'up').length}`, 100, 30)

  const tableData = hostsToExport.map((host) => [
    host.ip,
    host.hostname || 'N/A',
    host.nickname || '',
    host.mac || 'N/A',
    host.vendor || 'N/A',
    host.os_name || 'N/A',
    (host.status || 'unknown').toUpperCase(),
    (host.ports?.length || 0).toString(),
    host.last_seen ? new Date(host.last_seen).toLocaleDateString() : 'N/A'
  ])

  autoTable(pdf, {
    startY: 38,
    head: [['Dirección IP', 'Nombre de host', 'Apodo', 'Dirección MAC', 'Fabricante', 'SO', 'Estado', 'Puertos', 'Última vez visto']],
    body: tableData,
    theme: 'striped',
    headStyles: {
      fillColor: [34, 211, 238],
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      fontSize: 10,
      halign: 'center',
      cellPadding: 4
    },
    bodyStyles: {
      fontSize: 9,
      cellPadding: 3,
      textColor: [50, 50, 50]
    },
    alternateRowStyles: {
      fillColor: [245, 250, 252]
    },
    columnStyles: {
      0: { cellWidth: 28, fontStyle: 'bold', textColor: [34, 211, 238] },
      1: { cellWidth: 30 },
      2: { cellWidth: 28 },
      3: { cellWidth: 30, font: 'courier' },
      4: { cellWidth: 30 },
      5: { cellWidth: 25 },
      6: {
        cellWidth: 18,
        halign: 'center',
        fontStyle: 'bold'
      },
      7: { cellWidth: 16, halign: 'center' },
      8: { cellWidth: 25 }
    },
    didParseCell: function (data) {
      if (data.column.index === 6 && data.section === 'body') {
        if (data.cell.raw === 'UP') {
          data.cell.styles.textColor = [34, 197, 94]
          data.cell.styles.fillColor = [220, 252, 231]
        } else {
          data.cell.styles.textColor = [239, 68, 68]
          data.cell.styles.fillColor = [254, 226, 226]
        }
      }
    },
    margin: { top: 38, left: 14, right: 14 },
    didDrawPage: function (data) {
      const pageCount = pdf.internal.getNumberOfPages()
      const pageSize = pdf.internal.pageSize
      const pageHeight = pageSize.height || pageSize.getHeight()

      pdf.setFontSize(8)
      pdf.setTextColor(150)
      pdf.text(
        `Página ${data.pageNumber} de ${pageCount}`,
        pageSize.width / 2,
        pageHeight - 10,
        { align: 'center' }
      )

      pdf.text('Generado con ITE Scan', 14, pageHeight - 10)
    }
  })

  pdf.save(`ite_scan_${Date.now()}.pdf`)
}
