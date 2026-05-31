import React from 'react'
import { Table, Button, Card, Space, Tag, Input, Select, Row, Col } from 'antd'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { nodesApi, deviationsApi } from '../../api/client'

const Worksheet: React.FC = () => {
  const { studyId } = useParams<{ studyId: string }>()

  const { data: nodesData } = useQuery({
    queryKey: ['nodes', studyId],
    queryFn: () => nodesApi.list(studyId!),
    enabled: !!studyId,
  })

  const nodes = nodesData?.data?.items || []

  const columns = [
    { title: 'Ref', dataIndex: 'reference', width: 80 },
    { title: 'Node', dataIndex: 'name' },
    { title: 'Deviations', key: 'deviations', width: 120 },
    { title: 'Status', dataIndex: 'status', width: 100, render: (s: string) => <Tag>{s}</Tag> },
  ]

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>Worksheet</h1>
      
      <Card>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Input.Search placeholder="Search nodes or deviations..." />
          </Col>
          <Col span={8}>
            <Select placeholder="Filter by node" style={{ width: '100%' }} allowClear>
              {nodes.map((n: any) => (
                <Select.Option key={n.id} value={n.id}>{n.name}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col span={8}>
            <Select placeholder="Status filter" style={{ width: '100%' }} allowClear>
              <Select.Option value="open">Open</Select.Option>
              <Select.Option value="in_progress">In Progress</Select.Option>
              <Select.Option value="closed">Closed</Select.Option>
            </Select>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={nodes}
          rowKey="id"
          pagination={false}
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ padding: '8px 0' }}>
                <p><strong>Design Intent:</strong> {record.design_intent || 'N/A'}</p>
                <p><strong>Equipment:</strong> {record.equipment_type || 'N/A'}</p>
                <p><strong>Deviation Count:</strong> {record.deviation_count || 0}</p>
              </div>
            ),
          }}
        />
      </Card>
    </div>
  )
}

export default Worksheet