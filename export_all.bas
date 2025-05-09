Attribute VB_Name = "Módulo1"
Public Function export_all()
    Dim i As Integer
    For i = 0 To CurrentProject.ImportExportSpecifications.Count - 1
        DoCmd.RunSavedImportExport CurrentProject.ImportExportSpecifications(i).Name
    Next i
End Function
