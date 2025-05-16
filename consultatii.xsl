<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
  <html>
  <head>
    <title>Lista Consultațiilor</title>
    <style>
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid black; padding: 8px; text-align: left; }
      th { background-color: #f2f2f2; }
    </style>
  </head>
  <body>
    <h2>Lista Consultațiilor</h2>
    <table>
      <tr>
        <th>ID Consultatie</th>
        <th>Data</th>
        <th>Ora</th>
        <th>Pacient ID</th>
        <th>Medic ID</th>
        <th>Simptome</th>
        <th>Diagnostic (Cod)</th>
        <th>Diagnostic (Descriere)</th>
        <th>Indicatii Tratament</th>
      </tr>
      <xsl:apply-templates select="Clinica/Consultatii/Consultatie"/>
    </table>
  </body>
  </html>
</xsl:template>

<xsl:template match="Consultatie">
  <tr>
    <td><xsl:value-of select="@id_consultatie"/></td>
    <td><xsl:value-of select="Data"/></td>
    <td><xsl:value-of select="Ora"/></td>
    <td><xsl:value-of select="@id_pacient_ref"/></td>
    <td><xsl:value-of select="@id_medic_ref"/></td>
    <td><xsl:value-of select="Simptome"/></td>
    <td><xsl:value-of select="Diagnostic/CodICD10"/></td>
    <td><xsl:value-of select="Diagnostic/Descriere"/></td>
    <td><xsl:value-of select="Tratament/Indicatii"/></td>
    <!-- Add more columns if needed, e.g., for medication -->
  </tr>
</xsl:template>

</xsl:stylesheet>