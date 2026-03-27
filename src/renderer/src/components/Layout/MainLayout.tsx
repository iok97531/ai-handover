import { ReactNode } from 'react'

interface MainLayoutProps {
  sidebar: ReactNode
  children: ReactNode
}

export default function MainLayout({ sidebar, children }: MainLayoutProps) {
  return (
    <div className="flex h-screen w-screen overflow-hidden">
      {sidebar}
      <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
    </div>
  )
}
