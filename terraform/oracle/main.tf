provider "oci" {
  region = var.region
}

resource "oci_objectstorage_bucket" "docs" {
  namespace = var.namespace
  name      = var.bucket_name
  compartment_id = var.compartment_id
}

variable "region" {
  default = "us-ashburn-1"
}

variable "namespace" {
  description = "Object storage namespace"
}

variable "bucket_name" {
  default = "doc-assembler-storage"
}

variable "compartment_id" {
  description = "OCID of the compartment"
}
