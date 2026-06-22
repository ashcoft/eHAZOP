import React, { useState } from 'react'
import { Table, Button, Input, Tag, Card, Modal, Form, Select, message } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { studiesApi } from '../../api/client'

const StudyList: React.FC = () => {
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['studies', search],
    queryFn: () => studiesApi.list({ search: search || undefined, pageSize: 50 }),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => studiesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      message.success('Study created successfully')
      setIsModalOpen(false)
      form.resetFields()
    },
  })

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
      title: 'Facility',
      dataIndex: 'facility',
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
      title: 'Revision',
      dataIndex: 'revision',
      render: (rev: number) => `Rev ${rev}`,
    },
    {
      title: 'Members',
      dataIndex: 'member_count',
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}>Studies</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          New Study
        </Button>
      </div>

      <Card>
        <div style={{ marginBottom: 16 }}>
          <Input
            placeholder="Search studies..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 300 }}
          />
        </div>

        <Table
          columns={columns}
          dataSource={data?.data?.items}
          rowKey="id"
          loading={isLoading}
          pagination={{
            total: data?.data?.total,
            pageSize: 20,
            showTotal: (total) => `Total ${total} studies`,
          }}
        />
      </Card>

      <Modal
        title="Create New Study"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => createMutation.mutate(values)}
        >
          <Form.Item name="name" label="Study Name" rules={[{ required: true }]}>
            <Input placeholder="e.g., Substation A EHAZOP" />
          </Form.Item>
          <Form.Item name="study_type" label="Study Type" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="SAFAN">SAFAN (Personnel Safety)</Select.Option>
              <Select.Option value="SYSOP">SYSOP (System Operability)</Select.Option>
              <Select.Option value="OPTAN">OPTAN (Operator Task)</Select.Option>
              <Select.Option value="EHAZOP">EHAZOP (Electrical HAZOP)</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="facility" label="Facility" rules={[{ required: true }]}>
            <Input placeholder="e.g., Power Plant A" />
          </Form.Item>
          <Form.Item name="scope" label="Scope">
            <Input.TextArea rows={3} placeholder="Describe the study scope..." />
          </Form.Item>
          <Form.Item name="confidentiality" label="Confidentiality" initialValue="internal">
            <Select>
              <Select.Option value="public">Public</Select.Option>
              <Select.Option value="internal">Internal</Select.Option>
              <Select.Option value="confidential">Confidential</Select.Option>
              <Select.Option value="restricted">Restricted</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default StudyList