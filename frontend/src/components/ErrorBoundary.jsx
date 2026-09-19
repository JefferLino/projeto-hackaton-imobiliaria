import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center gap-3">
          <p className="text-lg font-medium">Algo deu errado ao carregar esta página.</p>
          <p className="text-sm text-muted-foreground">
            Tente recarregar ou navegar para outra seção.
          </p>
        </div>
      )
    }
    return this.props.children
  }
}
