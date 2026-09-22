const it = (await eda.lib_Device.getByLcscIds(['C109322'])).find(d => d.supplierId === 'C109322');
return it;
