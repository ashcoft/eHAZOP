import React from 'react'
import { Card, Tabs, Table, Button, Tag, Space } from 'antd'
import { UserOutlined, LockOutlined, SafetyOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { usersApi } from '../../api/client'
import { useAuthStore } from '../../store/authStore'

const Settings: React.FC = () => {
  const { user } = useAuthStore()

  const { data: usersData } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list(),
  })

  const users = usersData?.data?.items || []

  const userColumns = [
    { title: 'Name', dataIndex: 'full_name' },
    { title: 'Email', dataIndex: 'email' },
    { 
      title: 'Role', 
      dataIndex: 'role',
      render: (role: string) => {
        const colors: Record<string, string> = {
          admin: 'red',
          facilitator: 'blue',
          scribe: 'green',
          participant: 'default',
          viewer: 'default',
        }
        return <Tag color={colors[role]}>{role}</Tag>
      },
    },
    { title: 'Active', dataIndex: 'is_active', render: (v: boolean) => v ? 'Yes' : 'No' },
  ]

  const tabItems = [
    {
      key: 'profile',
      label: <span><UserOutlined /> Profile</span>,
      children: (
        <Card>
          <p><strong>Name:</strong> {user?.full_name}</p>
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>Role:</strong> {user?.role}</p>
          <Button type="primary">Edit Profile</Button>
        </Card>
      ),
    },
    {
      key: 'security',
      label: <span><LockOutlined /> Security</span>,
      children: (
        <Card title="Change Password">
          <p>Password change functionality</p>
        </Card>
      ),
    },
    {
      key: 'users',
      label: <span><SafetyOutlined /> User Management</span>,
      children: (
        <Card
          title="Users"
          extra={<Button type="primary">Add User</Button>}
        >
          <Table
            columns={userColumns}
            dataSource={users}
            rowKey="id"
            pagination={false}
          />
        </Card>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>Settings</h1>
      <Tabs items={tabItems} />
    </div>
  )
}

export default Settings