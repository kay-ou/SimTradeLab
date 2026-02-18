import { Layout } from 'antd'

const { Header, Content } = Layout

export default function App(): JSX.Element {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header>
        <span style={{ color: '#fff', fontSize: 18 }}>SimTradeLab</span>
      </Header>
      <Content style={{ padding: 24 }}>
        <p>Welcome to SimTradeLab</p>
      </Content>
    </Layout>
  )
}
