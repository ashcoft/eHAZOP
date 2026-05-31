import React, { useState } from 'react'
import { Form, Input, Button, Card, message, Tabs } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { authApi } from '../../api/client'
import { useAuthStore } from '../../store/authStore'

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const login = useAuthStore((state) => state.login)

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true)
    try {
      const response = await authApi.login(values.email, values.password)
      const { access_token, refresh_token } = response.data
      
      // Get user info
      const userResponse = await authApi.getMe()
      
      login(access_token, refresh_token, userResponse.data)
      message.success('Login successful!')
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #001529 0%, #003a70 100%)',
    }}>
      <Card
        style={{ width: 400, boxShadow: '0 4px 20px rgba(0,0,0,0.15)' }}
        title={<h2 style={{ textAlign: 'center', margin: 0 }}>EHAZOP Platform</h2>}
      >
        <Tabs
          defaultActiveKey="login"
          items={[
            {
              key: 'login',
              label: 'Sign In',
              children: (
                <Form
                  form={form}
                  name="login"
                  onFinish={onFinish}
                  layout="vertical"
                  requiredMark={false}
                >
                  <Form.Item
                    name="email"
                    label="Email"
                    rules={[
                      { required: true, message: 'Please enter your email' },
                      { type: 'email', message: 'Please enter a valid email' },
                    ]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="admin@ehazop.local"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    label="Password"
                    rules={[{ required: true, message: 'Please enter your password' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Enter password"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      block
                      size="large"
                    >
                      Sign In
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
            {
              key: 'register',
              label: 'Register',
              children: (
                <Form
                  name="register"
                  layout="vertical"
                  requiredMark={false}
                >
                  <Form.Item
                    name="email"
                    label="Email"
                    rules={[
                      { required: true, message: 'Please enter your email' },
                      { type: 'email', message: 'Please enter a valid email' },
                    ]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="user@example.com"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item name="password" label="Password">
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Min 8 characters"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item name="fullName" label="Full Name">
                    <Input
                      placeholder="John Doe"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" block size="large" disabled>
                      Registration (Contact Admin)
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}

export default LoginPage