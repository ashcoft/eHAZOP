import React, { useState } from 'react'
import { Card, Button, Space, message } from 'antd'
import { FilePdfOutlined, FileExcelOutlined, DownloadOutlined } from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { reportsApi } from '../../api/client'

const Reports: React.FC = () => {
  const { studyId } = useParams<{ studyId: string }>()
  const [pdfLoading, setPdfLoading] = useState(false)
  const [excelLoading, setExcelLoading] = useState(false)

  const pdfMutation = useMutation({
    mutationFn: () => reportsApi.generatePDF(studyId!),
    onSuccess: () => {
      message.success('PDF report generated successfully')
      setPdfLoading(false)
    },
    onError: () => {
      message.error('Failed to generate PDF report')
      setPdfLoading(false)
    },
  })

  const excelMutation = useMutation({
    mutationFn: () => reportsApi.generateExcel(studyId!),
    onSuccess: () => {
      message.success('Excel report generated successfully')
      setExcelLoading(false)
    },
    onError: () => {
      message.error('Failed to generate Excel report')
      setExcelLoading(false)
    },
  })

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>Reports</h1>

      <Card title="Study Reports">
        <p style={{ marginBottom: 24 }}>
          Generate comprehensive reports for the study. Reports include all nodes, deviations,
          risk assessments, and recommendations.
        </p>

        <Space size="large">
          <Button
            type="primary"
            icon={<FilePdfOutlined />}
            size="large"
            loading={pdfLoading}
            onClick={() => {
              setPdfLoading(true)
              pdfMutation.mutate()
            }}
          >
            Generate PDF Report
          </Button>

          <Button
            icon={<FileExcelOutlined />}
            size="large"
            loading={excelLoading}
            onClick={() => {
              setExcelLoading(true)
              excelMutation.mutate()
            }}
          >
            Generate Excel Report
          </Button>
        </Space>
      </Card>

      <Card title="Recent Reports" style={{ marginTop: 24 }}>
        <p style={{ color: '#999' }}>No reports generated yet. Generate your first report above.</p>
      </Card>
    </div>
  )
}

export default Reports