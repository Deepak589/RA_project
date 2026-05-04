import BottomNav from "./BottomNav.jsx";
import PageHeader from "./PageHeader.jsx";

export default function AppLayout({ title, children, action, back = false }) {
  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      <PageHeader title={title} action={action} back={back} />
      <main className="mx-auto w-full max-w-md space-y-4 px-4 py-4">{children}</main>
      <BottomNav />
    </div>
  );
}
