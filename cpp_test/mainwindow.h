#ifndef MAINWINDOW_H
#define MAINWINDOW_H
#include <QMainWindow>
#include <BStimulator.h>

namespace Ui {
class MainWindow;
}


class MainWindow : public QMainWindow {
	Q_OBJECT

public:
	explicit MainWindow(QWidget *parent);
	~MainWindow() noexcept override;

private:
	void refresh_devices();
	void connect_device();

	std::unique_ptr<Ui::MainWindow> ui; // window pointer
	BStimulator cerestim;
};

#endif // MAINWINDOW_H
