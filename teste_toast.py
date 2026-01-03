from winotify import Notification

toast = Notification(
    app_id="TesteNotificacaoPython",
    title="Teste",
    msg="Se isso aparecer, está funcionando"
)

toast.show()
