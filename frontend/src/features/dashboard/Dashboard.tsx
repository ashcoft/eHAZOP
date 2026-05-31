import React from 'react'
import { Card, Row, Col, Statistic, Table, List, Tag, Progress } from 'antd'
import { 
  FileTextOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined,
  WarningOutlined,
  TeamOutlined,
  SafetyOutlined
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { studiesApi, actionsApi } from '../../api/client'
import { Link } from 'react-router-dom'

const Dashboard: React.FC = () => {
  const { data: studiesData } = useQuery({
    queryKey: ['studies'],
    queryFn: () => studiesApi.list({ pageSize: 5 }),
  })

  const { data: actionsData } = useQuery({
    queryKey: ['overdue-actions'],
    queryFn: () => actionsApi.getOverdue(),
  })

  const studies = studiesData?.data?.items || []
  const overdueActions = actionsData?.data?.items || []

  const stats = {
    totalStudies: studiesData?.data?.total || 0,
    inProgress: studies.filter((s: any) => s.status === 'in_progress').length,
    completed: studies.filter((s: any) => s.status === 'completed').length,
    overdueActions: overdueActions.length,
  }

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      render: (text: string, record: any) => (
        <Link to={`/studies/${record.id}`}>{text}</Link>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'study_type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = {
          draft: 'default',
          in_progress: 'processing',
          review: 'warning',
          completed: 'success',
          archived: 'default',
        }
        return <Tag color={colors[status] || 'default'}>{status}</Tag>
      },
    },
    {
      title: 'Facility',
      dataIndex: 'facility',
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>Dashboard</h1>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Studies"
              value={stats.totalStudies}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="In Progress"
              value={stats.inProgress}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Completed"
              value={stats.completed}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Overdue Actions"
              value={stats.overdueActions}
              prefix={<WarningOutlined />}
              valueStyle={{ color: stats.overdueActions > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={16}>
          <Card 
            title="Recent Studies" 
            extra={<Link to="/studies">View All</Link>}
          >
            <Table
              columns={columns}
              dataSource={studies}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card 
            title="Overdue Actions" 
            extra={<Link to="/actions?status=overdue">View All</Link>}
          >
            {overdueActions.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#52c41a' }}>
                <CheckCircleOutlined style={{ fontSize: 32 }} />
                <p>No overdue actions!</p>
              </div>
            ) : (
              <List
                size="small"
                dataSource={overdueActions.slice(0, 5)}
                renderItem={(item: any) => (
                  <List.Item>
                    <Tag color="red">{item.reference}</Tag>
                    <span style={{ marginLeft: 8 }}>{item.description}</span>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="Quick Actions">
            <Row gutter={16}>
              <Col span={12}>
                <Link to="/studies/new">
                  <Card hoverable style={{ textAlign: 'center' }}>
                    <SafetyOutlined style={{ fontSize: 32, color: '#1890ff' }} />
                    <p>Create New Study</p>
                  </Card>
                </Link>
              </Col>
              <Col span={12}>
                <Link to="/settings">
                  <Card hoverable style={{ textAlign: 'center' }}>
                    <TeamOutlined style={{ fontSize: 32, color: '#1890ff' }} />
                    <p>Manage Users</p>
                  </Card>
                </Link>
              </Col>
            </Row>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Risk Distribution">
            <Row gutter={16}>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <Progress type="circle" percent={30} size={60} strokeColor="#52c41a" />
                  <p>Low</p>
                </div>
              </Col>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <Progress type="circle" percent={40} size={60} strokeColor="#faad14" />
                  <p>Medium</p>
                </div>
              </Col>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <Progress type="circle" percent={20} size={60} strokeColor="#fa8c16" />
                  <p>High</p>
                </div>
              </Col>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <Progress type="circle" percent={10} size={60} strokeColor="#ff4d4f" />
                  <p>Very High</p>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard