-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: beneficios_data
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `apoyo`
--

DROP TABLE IF EXISTS `apoyo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `apoyo` (
  `ID` int unsigned NOT NULL AUTO_INCREMENT,
  `CI_autorizado` int DEFAULT NULL,
  `Nombre_autorizado` varchar(150) DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `Fecha` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `apoyo`
--

LOCK TABLES `apoyo` WRITE;
/*!40000 ALTER TABLE `apoyo` DISABLE KEYS */;
/*!40000 ALTER TABLE `apoyo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autorizados`
--

DROP TABLE IF EXISTS `autorizados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `autorizados` (
  `ID` int unsigned NOT NULL AUTO_INCREMENT,
  `beneficiado` int NOT NULL,
  `Nombre` varchar(150) NOT NULL,
  `Cedula` int NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `beneficiado` (`beneficiado`),
  CONSTRAINT `autorizados_ibfk_1` FOREIGN KEY (`beneficiado`) REFERENCES `personal` (`Cedula`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autorizados`
--

LOCK TABLES `autorizados` WRITE;
/*!40000 ALTER TABLE `autorizados` DISABLE KEYS */;
/*!40000 ALTER TABLE `autorizados` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `delivery`
--

DROP TABLE IF EXISTS `delivery`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `delivery` (
  `ID` int unsigned NOT NULL AUTO_INCREMENT,
  `Time_box` datetime NOT NULL,
  `Data_ID` int NOT NULL,
  `Staff_ID` int NOT NULL,
  `Observation` varchar(250) DEFAULT NULL,
  `Lunch` tinyint unsigned DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `Data_ID` (`Data_ID`),
  KEY `idx_time_box` (`Time_box`),
  KEY `idx_staff_id` (`Staff_ID`),
  KEY `idx_lunch` (`Lunch`),
  CONSTRAINT `delivery_ibfk_1` FOREIGN KEY (`Data_ID`) REFERENCES `personal` (`Cedula`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `delivery_ibfk_2` FOREIGN KEY (`Staff_ID`) REFERENCES `usuarios` (`C_I`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `delivery`
--

LOCK TABLES `delivery` WRITE;
/*!40000 ALTER TABLE `delivery` DISABLE KEYS */;
/*!40000 ALTER TABLE `delivery` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personal`
--

DROP TABLE IF EXISTS `personal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personal` (
  `ID` int unsigned NOT NULL AUTO_INCREMENT,
  `Cedula` int NOT NULL,
  `Name_Com` varchar(150) NOT NULL,
  `Code` int DEFAULT NULL,
  `Location_Physical` varchar(200) DEFAULT NULL,
  `Location_Admin` varchar(200) DEFAULT NULL,
  `manually` tinyint(1) DEFAULT '0',
  `Estatus` tinyint unsigned NOT NULL DEFAULT '1',
  `ESTADOS` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Cedula` (`Cedula`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personal`
--

LOCK TABLES `personal` WRITE;
/*!40000 ALTER TABLE `personal` DISABLE KEYS */;
/*!40000 ALTER TABLE `personal` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_history`
--

DROP TABLE IF EXISTS `user_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_history` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `cedula` int NOT NULL,
  `Name_user` varchar(150) NOT NULL,
  `Name_personal` varchar(150) DEFAULT NULL,
  `cedula_personal` int DEFAULT NULL,
  `Name_autorizado` varchar(150) DEFAULT NULL,
  `Cedula_autorizado` int DEFAULT NULL,
  `action` varchar(150) NOT NULL,
  `time_login` datetime NOT NULL,
  `time_finish` datetime DEFAULT NULL,
  `session_duration` int GENERATED ALWAYS AS (timestampdiff(SECOND,`time_login`,`time_finish`)) VIRTUAL,
  PRIMARY KEY (`id`),
  KEY `idx_time_login` (`time_login`),
  KEY `idx_cedula` (`cedula`),
  KEY `idx_cedula_personal` (`cedula_personal`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_history`
--

LOCK TABLES `user_history` WRITE;
/*!40000 ALTER TABLE `user_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `ID` int unsigned NOT NULL AUTO_INCREMENT,
  `C_I` int NOT NULL,
  `username` varchar(100) DEFAULT NULL,
  `Password` varchar(255) NOT NULL,
  `Super_Admin` tinyint(1) DEFAULT '0',
  `estado` enum('activo','suspendido') DEFAULT 'activo',
  PRIMARY KEY (`ID`),
  UNIQUE KEY `C_I` (`C_I`),
  UNIQUE KEY `username` (`username`),
  CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`C_I`) REFERENCES `personal` (`Cedula`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (2,30799436,'JFERNANDOB2','$2b$12$6B2eAr0eRRG4s4E5.C/hQuzdO/HmTOv28XUz6uBr.81q46tg0kfJi',1,'activo');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-24 18:16:30
