import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, Row, Col, Descriptions, Tag, Button, Tabs, Table, Space } from 'antd'
import { 
  ArrowLeftOutlined, 
  PlayCircleOutlined, 
  CheckCircleOutlined,
  FileTextOutlined,
  TeamOutlined
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { studiesApi, nodesApi, actionsApi } from '../../api/client'

const StudyDetail: React.FC = () => {
  const { studyId } = useParams<{ studyId: string }>()

  const { data: study } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => studiesApi.get(studyId!),
    enabled: !!studyId,
  })

  const { data: nodesData } = useQuery({
    queryKey: ['nodes', studyId],
    queryFn: () => nodesApi.list(studyId!),
    enabled: !!studyId,
  })

  const { data: actionsSummary } = useQuery({
    queryKey: ['actions-summary', studyId],
    queryFn: () => actionsApi.getSummary(studyId!),
    enabled: !!studyId,
  })

  const nodes = nodesData?.data?.items || []
  const summary = actionsSummary?.data || {}

  const statusColors: Record<string, string> = {
    draft: 'default',
    in_progress: 'processing',
    review: 'warning',
    completed: 'success',
    archived: 'default',
  }

  const nodeColumns = [
    { title: 'Reference', dataIndex: 'reference', width: 100 },
    { title: 'Name', dataIndex: 'name' },
    { title: 'Equipment Type', dataIndex: 'equipment_type' },
    { title: 'Deviations', dataIndex: 'deviation_count', width: 100 },
  ]

  const tabItems = [
    {
      key: 'nodes',
      label: `Nodes (${nodes.length})`,
      children: (
        <Table
          columns={nodeColumns}
          dataSource={nodes}
          rowKey="id"
          pagination={false}
          size="small"
        />
      ),
    },
    {
      key: 'actions',
      label: `Actions (${summary.total || 0})`,
      children: (
        <Row gutter={16}>
          <Col span={6}><Card>Open: {summary.open || 0}</Card></Col>
          <Col span={6}><Card>In Progress: {summary.in_progress || 0}</Card></Col>
          <Col span={6}><Card>Completed: {summary.completed || 0}</Card></Col>
          <Col span={6}><Card>Overdue: {summary.overdue || 0}</Card></Col>
        </Row>
      ),
    },
    {
      key: 'members',
      label: <span><TeamOutlined /> Members</span>,
      children: <p>Member management coming soon</p>,
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Link to="/studies">
        <Button icon={<ArrowLeftOutlined />}>Back to Studies</Button>
      </Link>

      {study && (
        <>
          <Card style={{ marginTop: 16 }}>
            <Descriptions
              title={
                <span>
                  {study.data.name}
                  <Tag color={statusColors[study.data.status]} style={{ marginLeft: 8 }}>
                    {study.data.status}
                  </Tag>
                </span>
              }
              extra={
                <Space>
                  {study.data.status === 'draft' && (
                    <Button type="primary" icon={<PlayCircleOutlined />}>
                      Start Study
                    </Button>
                  )}
                  {study.data.status === 'in_progress' && (
                    <Button type="primary" icon={<CheckCircleOutlined />}>
                      Complete Study
                    </Button>
                  )}
                  <Link to={`/studies/${studyId}/worksheet`}>
                    <Button icon={<FileTextOutlined />}>Open Worksheet</Button>
                  </Link>
                  <Link to={`/studies/${studyId}/reports`}>
                    <Button>Generate Report</Button>
                  </Link>
                </Space>
              }
            >
              <Descriptions.Item label="Study Type">
                <Tag color="blue">{study.data.study_type}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Facility">{study.data.facility}</Descriptions.Item>
              <Descriptions.Item label="Revision">Rev {study.data.revision}</Descriptions.Item>
              <Descriptions.Item label="Confidentiality">{study.data.confidentiality}</Descriptions.Item>
              <Descriptions.Item label="Scope" span={2}>{study.data.scope || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="Description" span={3}>{study.data.description || 'N/A'}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Card style={{ marginTop: 16 }}>
            <Tabs items={tabItems} />
          </Card>
        </>
      )}
    </div>
  )
}

export default StudyDetail