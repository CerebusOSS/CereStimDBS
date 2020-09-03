#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QDateTime>
#include <QDebug>
#include <QFileDialog>
#include <QMessageBox>
#include <QSettings>
#include <QStandardPaths>

#include <string>
#include <vector>


MainWindow::MainWindow(QWidget *parent)
	: QMainWindow(parent), ui(new Ui::MainWindow) {
	ui->setupUi(this);
	
	connect(ui->refresh_pushButton, &QPushButton::clicked, this, &MainWindow::refresh_devices);
	connect(ui->connect_pushButton, &QPushButton::clicked, this, &MainWindow::connect_device);
}

MainWindow::~MainWindow()
{
	// TODO: disconnect
}

void MainWindow::refresh_devices()
{
	ui->device_comboBox->clear();

	std::vector<UINT32> deviceList;
	BResult res = cerestim.scanForDevices(deviceList); //populate device list with SN of connected devices
	for (int i = 0; i < deviceList.size(); i++) {
		ui->device_comboBox->addItem(QString::number(deviceList.at(i)));
	}

}

MainWindow::connect_device()
{
	ui->device_comboBox->currentIndex();
}
